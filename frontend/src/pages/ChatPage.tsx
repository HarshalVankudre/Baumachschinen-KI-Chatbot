import { useState, useEffect, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import { chatService } from '@/services/chatService';
import { useToast } from '@/hooks/use-toast';
import type { Message } from '@/types';
import { Header } from '@/components/layout/Header';
import { ConversationSidebar } from '@/components/chat/ConversationSidebar';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { MessageInput } from '@/components/chat/MessageInput';
import { EmptyState } from '@/components/shared/EmptyState';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { MessageSquare, Loader2, Settings2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export default function ChatPage() {
  const { activeConversationId, setActiveConversation } = useChatStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [searchAlpha, setSearchAlpha] = useState(0.75); // Default: 75% vector, 25% keyword
  const [enableRerank, setEnableRerank] = useState(true); // Default: reranking enabled
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch conversations
  const { data: conversations = [], isLoading: conversationsLoading, refetch: refetchConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatService.getConversations(),
  });

  // Fetch messages for active conversation
  const { data: currentConversation, isLoading: messagesLoading } = useQuery({
    queryKey: ['conversation', activeConversationId],
    queryFn: () =>
      activeConversationId
        ? chatService.getConversation(activeConversationId)
        : null,
    enabled: !!activeConversationId,
  });

  // Update messages when conversation changes
  useEffect(() => {
    if (currentConversation?.messages) {
      setMessages(currentConversation.messages);
    } else {
      setMessages([]);
    }
  }, [currentConversation]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Set initial conversation if none is active
  useEffect(() => {
    if (conversations.length > 0 && !activeConversationId) {
      setActiveConversation(conversations[0].conversation_id);
    }
  }, [conversations, activeConversationId, setActiveConversation]);

  // Handle rate limit events
  useEffect(() => {
    const handleRateLimit = (event: Event) => {
      const customEvent = event as CustomEvent;
      toast({
        title: 'Rate Limit Exceeded',
        description: customEvent.detail.message,
        variant: 'destructive',
      });
    };

    window.addEventListener('rate-limit-exceeded', handleRateLimit);
    return () => window.removeEventListener('rate-limit-exceeded', handleRateLimit);
  }, [toast]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Create new conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: () => chatService.createConversation('New Conversation'),
    onSuccess: (newConv) => {
      refetchConversations();
      setActiveConversation(newConv.conversation_id);
      setMessages([]);
      toast({
        title: 'Erfolgreich',
        description: 'Neue Konversation erstellt',
      });
    },
    onError: () => {
      toast({
        title: 'Fehler',
        description: 'Konversation konnte nicht erstellt werden',
        variant: 'destructive',
      });
    },
  });

  // Rename conversation mutation
  const renameConversationMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      chatService.updateConversation(id, title),
    onSuccess: () => {
      refetchConversations();
      toast({
        title: 'Erfolgreich',
        description: 'Konversation umbenannt',
      });
    },
    onError: () => {
      toast({
        title: 'Fehler',
        description: 'Konversation konnte nicht umbenannt werden',
        variant: 'destructive',
      });
    },
  });

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => chatService.deleteConversation(id),
    onSuccess: (_, deletedId) => {
      refetchConversations();
      if (activeConversationId === deletedId) {
        setActiveConversation(null);
        setMessages([]);
      }
      toast({
        title: 'Erfolgreich',
        description: 'Konversation gelöscht',
      });
    },
    onError: () => {
      toast({
        title: 'Fehler',
        description: 'Konversation konnte nicht gelöscht werden',
        variant: 'destructive',
      });
    },
  });

  const handleSendMessage = async (content: string) => {
    if (!activeConversationId) {
      toast({
        title: 'Fehler',
        description: 'Bitte wählen oder erstellen Sie zuerst eine Konversation',
        variant: 'destructive',
      });
      return;
    }

    const userMessage: Message = {
      message_id: `temp-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);
    setStreamingMessage('');

    try {
      const response = await chatService.sendMessage(activeConversationId, content, {
        alpha: searchAlpha,
        enableRerank,
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No response body');

      let buffer = '';
      let accumulatedMessage = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          // Skip empty lines
          if (!line.trim()) {
            continue;
          }

          // SSE comment lines (keepalive pings)
          if (line.startsWith(':')) {
            continue;
          }

          // SSE data lines
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            // Skip empty data lines
            if (!data) {
              continue;
            }

            // Legacy support for [DONE] signal
            if (data === '[DONE]') {
              setIsStreaming(false);
              const assistantMessage: Message = {
                message_id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: accumulatedMessage,
                timestamp: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMessage]);
              setStreamingMessage('');
              refetchConversations();
              queryClient.invalidateQueries({
                queryKey: ['conversation', activeConversationId],
              });
              return;
            }

            try {
              // Parse the JSON data
              const parsed = JSON.parse(data);

              // Handle different SSE event types
              if (parsed.type === 'token') {
                // Stream token content
                accumulatedMessage += parsed.content;
                setStreamingMessage(accumulatedMessage);
              } else if (parsed.type === 'complete') {
                // Response complete - save message with metadata
                setIsStreaming(false);
                const assistantMessage: Message = {
                  message_id: parsed.message_id || `assistant-${Date.now()}`,
                  role: 'assistant',
                  content: accumulatedMessage,
                  timestamp: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, assistantMessage]);
                setStreamingMessage('');
                refetchConversations();
                queryClient.invalidateQueries({
                  queryKey: ['conversation', activeConversationId],
                });

                // Log metadata if available
                if (parsed.token_count || parsed.response_time_ms) {
                  console.log('Response metadata:', {
                    tokens: parsed.token_count,
                    time: parsed.response_time_ms,
                    sources: parsed.sources?.length || 0
                  });
                }
                return;
              } else if (parsed.type === 'source') {
                // Source citations received
                console.log('Sources received:', parsed.sources);
              } else if (parsed.type === 'error') {
                // Error occurred
                console.error('SSE Error:', parsed.message, parsed.details);
                setIsStreaming(false);
                setStreamingMessage('');
                toast({
                  title: 'Fehler',
                  description: parsed.message || 'Ein Fehler ist aufgetreten',
                  variant: 'destructive',
                });
                // Remove the user message on error
                setMessages((prev) => prev.filter((m) => m.message_id !== userMessage.message_id));
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
              console.error('Problematic data:', data);
              console.error('Original line:', line);
              // Continue processing other events instead of breaking
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsStreaming(false);
      setStreamingMessage('');
      toast({
        title: 'Fehler',
        description: 'Nachricht konnte nicht gesendet werden. Bitte versuchen Sie es erneut.',
        variant: 'destructive',
      });
      // Remove the user message on error
      setMessages((prev) => prev.filter((m) => m.message_id !== userMessage.message_id));
    }
  };

  const handleEditMessage = (_messageId: string) => {
    toast({
      title: 'Demnächst verfügbar',
      description: 'Die Nachrichtenbearbeitung wird bald verfügbar sein',
    });
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />

      <div className="flex-1 flex overflow-hidden">
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={setActiveConversation}
          onNewConversation={() => createConversationMutation.mutate()}
          onRenameConversation={(id, title) =>
            renameConversationMutation.mutate({ id, title })
          }
          onDeleteConversation={(id) => deleteConversationMutation.mutate(id)}
          loading={conversationsLoading}
        />

        <div className="flex-1 flex flex-col">
        {!activeConversationId ? (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={MessageSquare}
              title="Keine Konversation ausgewählt"
              message="Wählen Sie eine Konversation aus der Seitenleiste aus oder erstellen Sie eine neue, um zu beginnen."
              actionLabel="Neue Konversation"
              onAction={() => createConversationMutation.mutate()}
            />
          </div>
        ) : (
          <>
            <ScrollArea className="flex-1 px-6 py-6 scrollbar-premium">
              {messagesLoading ? (
                <div className="space-y-6 max-w-4xl mx-auto">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex gap-4 animate-pulse">
                      <Skeleton className="h-24 w-3/4 rounded-xl" />
                    </div>
                  ))}
                </div>
              ) : messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <EmptyState
                    icon={MessageSquare}
                    title="Konversation starten"
                    message="Senden Sie eine Nachricht, um mit dem Baumaschinen-KI-Assistenten zu chatten."
                  />
                </div>
              ) : (
                <div className="max-w-4xl mx-auto">
                  {messages.map((message) => (
                    <MessageBubble
                      key={message.message_id}
                      message={message}
                      conversationId={activeConversationId || undefined}
                      onEdit={handleEditMessage}
                    />
                  ))}

                  {isStreaming && streamingMessage && (
                    <MessageBubble
                      message={{
                        message_id: 'streaming',
                        role: 'assistant',
                        content: streamingMessage,
                        timestamp: new Date().toISOString(),
                      }}
                      conversationId={activeConversationId || undefined}
                    />
                  )}

                  {isStreaming && !streamingMessage && (
                    <div className="flex justify-start p-4 animate-fade-in">
                      <div className="flex items-center gap-3 text-muted-foreground bg-muted/30 px-4 py-3 rounded-xl border border-border/50">
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        <span className="font-medium">Denke nach...</span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* Hybrid Search Settings */}
            <div className="border-t border-border/50 bg-muted/30 px-6 py-3">
              <div className="max-w-4xl mx-auto space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Settings2 className="h-4 w-4" />
                  <span>Sucheinstellungen</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Alpha Slider */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="search-alpha" className="text-sm">
                        Suche-Balance: {(searchAlpha * 100).toFixed(0)}% Vektor
                      </Label>
                      <span className="text-xs text-muted-foreground">
                        {searchAlpha === 0 ? 'Nur Schlüsselwörter' :
                         searchAlpha === 1 ? 'Nur Semantik' :
                         'Hybrid'}
                      </span>
                    </div>
                    <Slider
                      id="search-alpha"
                      min={0}
                      max={1}
                      step={0.05}
                      value={[searchAlpha]}
                      onValueChange={(value: number[]) => setSearchAlpha(value[0])}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Schlüsselwort (BM25)</span>
                      <span>Semantisch (Vektor)</span>
                    </div>
                  </div>

                  {/* Reranking Toggle */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="enable-rerank" className="text-sm">
                        Cohere Reranking
                      </Label>
                      <Switch
                        id="enable-rerank"
                        checked={enableRerank}
                        onCheckedChange={setEnableRerank}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Verbessert die Relevanz der Suchergebnisse durch intelligentes Neuranking
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <MessageInput
              onSend={handleSendMessage}
              disabled={isStreaming}
              placeholder="Fragen Sie mich alles über Baumaschinen..."
            />
          </>
        )}
        </div>
      </div>
    </div>
  );
}
