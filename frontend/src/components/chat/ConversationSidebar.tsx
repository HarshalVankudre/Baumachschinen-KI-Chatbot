import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SearchInput } from '@/components/shared/SearchInput';
import { EmptyState } from '@/components/shared/EmptyState';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import type { Conversation } from '@/types';
import { Plus, MessageSquare, Trash2, Edit2, GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  applySavedOrder,
  saveConversationOrder,
  cleanupConversationOrder,
} from '@/lib/conversationOrder';

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onDeleteConversation: (id: string) => void;
  loading?: boolean;
}

// Sortable conversation item component
interface SortableConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editingTitle: string;
  onSelect: () => void;
  onStartEdit: () => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onDeleteClick: () => void;
  onEditTitleChange: (value: string) => void;
}

function SortableConversationItem({
  conversation,
  isActive,
  isEditing,
  editingTitle,
  onSelect,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDeleteClick,
  onEditTitleChange,
}: SortableConversationItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: conversation.conversation_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength ? title.slice(0, maxLength) + '...' : title;
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group relative rounded-lg p-3 cursor-pointer transition-colors',
        'hover:bg-muted border-2',
        isActive
          ? 'bg-primary/10 border-primary'
          : 'bg-background border-transparent',
        isDragging && 'z-50 shadow-lg'
      )}
      onClick={onSelect}
    >
      {isEditing ? (
        <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
          <input
            type="text"
            value={editingTitle}
            onChange={(e) => onEditTitleChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSaveEdit();
              if (e.key === 'Escape') onCancelEdit();
            }}
            className="w-full px-2 py-1 text-sm border rounded"
            autoFocus
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={onSaveEdit} className="flex-1">
              Speichern
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onCancelEdit}
              className="flex-1"
            >
              Abbrechen
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2">
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing pt-1 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => e.stopPropagation()}
          >
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm truncate">
              {truncateTitle(conversation.title)}
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              {conversation.message_count}{' '}
              {conversation.message_count === 1 ? 'Nachricht' : 'Nachrichten'}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(conversation.last_message_at), {
                addSuffix: true,
                locale: de,
              })}
            </p>
          </div>

          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                onStartEdit();
              }}
              aria-label="Rename conversation"
            >
              <Edit2 className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteClick();
              }}
              aria-label="Delete conversation"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onRenameConversation,
  onDeleteConversation,
  loading = false,
}: ConversationSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [orderedConversations, setOrderedConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Apply saved order when conversations change
  useEffect(() => {
    const ordered = applySavedOrder(conversations);
    setOrderedConversations(ordered);

    // Clean up localStorage from deleted conversations
    const existingIds = conversations.map(c => c.conversation_id);
    cleanupConversationOrder(existingIds);
  }, [conversations]);

  // Setup drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Require 8px movement before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const filteredConversations = orderedConversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleStartEdit = (conv: Conversation) => {
    setEditingId(conv.conversation_id);
    setEditingTitle(conv.title);
  };

  const handleSaveEdit = () => {
    if (editingId && editingTitle.trim()) {
      onRenameConversation(editingId, editingTitle.trim());
      setEditingId(null);
      setEditingTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const handleDelete = () => {
    if (deleteConfirmId) {
      onDeleteConversation(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) {
      return;
    }

    setOrderedConversations((items) => {
      const oldIndex = items.findIndex((item) => item.conversation_id === active.id);
      const newIndex = items.findIndex((item) => item.conversation_id === over.id);

      const newOrder = arrayMove(items, oldIndex, newIndex);

      // Save new order to localStorage
      const conversationIds = newOrder.map(c => c.conversation_id);
      saveConversationOrder(conversationIds);

      return newOrder;
    });
  };

  return (
    <div className="w-80 border-r bg-muted/20 flex flex-col h-full">
      <div className="p-4 border-b space-y-4">
        <Button
          onClick={onNewConversation}
          className="w-full"
          variant="accent"
          disabled={loading}
        >
          <Plus className="h-4 w-4 mr-2" />
          Neue Konversation
        </Button>

        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Konversationen durchsuchen..."
        />
      </div>

      <ScrollArea className="flex-1 scroll-smooth">
        {filteredConversations.length === 0 ? (
          <div className="p-4">
            {searchQuery ? (
              <EmptyState
                icon={MessageSquare}
                title="Keine Ergebnisse"
                message="Keine Konversationen entsprechen Ihrer Suche."
              />
            ) : (
              <EmptyState
                icon={MessageSquare}
                title="Noch keine Konversationen"
                message="Starten Sie eine neue Konversation, um zu beginnen."
                actionLabel="Neue Konversation"
                onAction={onNewConversation}
              />
            )}
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={filteredConversations.map(c => c.conversation_id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="p-2 space-y-1">
                {filteredConversations.map((conv) => (
                  <SortableConversationItem
                    key={conv.conversation_id}
                    conversation={conv}
                    isActive={activeConversationId === conv.conversation_id}
                    isEditing={editingId === conv.conversation_id}
                    editingTitle={editingTitle}
                    onSelect={() => onSelectConversation(conv.conversation_id)}
                    onStartEdit={() => handleStartEdit(conv)}
                    onSaveEdit={handleSaveEdit}
                    onCancelEdit={handleCancelEdit}
                    onDeleteClick={() => setDeleteConfirmId(conv.conversation_id)}
                    onEditTitleChange={setEditingTitle}
                  />
                ))}
              </div>
            </SortableContext>

            <DragOverlay>
              {activeId ? (
                <div className="rounded-lg p-3 bg-background border-2 border-primary shadow-lg opacity-90">
                  <div className="flex items-start gap-2">
                    <GripVertical className="h-4 w-4 text-muted-foreground pt-1" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">
                        {filteredConversations.find(c => c.conversation_id === activeId)?.title}
                      </h3>
                    </div>
                  </div>
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        )}
      </ScrollArea>

      <AlertDialog
        open={deleteConfirmId !== null}
        onOpenChange={(open) => !open && setDeleteConfirmId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Konversation löschen</AlertDialogTitle>
            <AlertDialogDescription>
              Sind Sie sicher, dass Sie diese Konversation löschen möchten? Diese Aktion kann nicht
              rückgängig gemacht werden.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive">
              Löschen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
