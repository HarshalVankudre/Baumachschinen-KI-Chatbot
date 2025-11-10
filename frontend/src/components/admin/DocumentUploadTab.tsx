import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, Trash2, X, CheckCircle, AlertCircle, Clock, Loader2 } from 'lucide-react';
import { useServerQueue } from '@/hooks/useServerQueue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { DataTable, type Column } from '@/components/shared/DataTable';
import { documentService } from '@/services/documentService';
import { toast } from 'sonner';
import type { Document } from '@/types';
import { format } from 'date-fns';
import { translateCategory } from '@/utils/translations';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.ppt', '.jpg', '.jpeg', '.png', '.gif'];

export function DocumentUploadTab() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [category, setCategory] = useState<string>('');
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Server-side queue management
  const serverQueue = useServerQueue();

  // Fetch documents with auto-refresh when there are queue items or processing activity
  const { data: documentsData, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentService.getDocuments(),
    refetchInterval: () => {
      // Refresh every 2 seconds if there are pending items or processing stats
      const hasQueueItems = serverQueue.queue.length > 0;
      const hasProcessingActivity = serverQueue.stats.processing > 0;
      return hasQueueItems || hasProcessingActivity ? 2000 : false;
    },
    refetchIntervalInBackground: true,
  });

  // Store active SSE connections to prevent duplicates and ensure cleanup
  const activeStreamsRef = useRef<Map<string, EventSource>>(new Map());

  // Connect to SSE stream for real-time document processing updates
  const connectToDocumentStream = useCallback((documentId: string, retryCount = 0) => {
    // Check if already connected to this document
    if (activeStreamsRef.current.has(documentId)) {
      console.log('Already connected to document stream:', documentId);
      return;
    }

    // EventSource automatically includes cookies for authentication
    const eventSource = new EventSource(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/documents/stream/${documentId}`,
      { withCredentials: true }
    );

    // Store in active connections
    activeStreamsRef.current.set(documentId, eventSource);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle different event types
        if (data.type === 'connected') {
          console.log('Connected to document stream:', documentId);
        } else if (data.type === 'done') {
          console.log('Document processing stream closed');
          eventSource.close();
          activeStreamsRef.current.delete(documentId);
        } else if (data.type === 'error') {
          console.error('SSE error:', data.message);
          eventSource.close();
          activeStreamsRef.current.delete(documentId);
        } else if (data.processing_status) {
          // Status update - refetch queries to get latest data
          console.log('Document status update:', data.processing_status);
          queryClient.refetchQueries({ queryKey: ['documents'] });

          // Show toast on completion
          if (data.processing_status === 'completed') {
            toast.success('Dokument erfolgreich verarbeitet', {
              description: `Das Dokument wurde in ${data.chunk_count || 0} Abschnitte aufgeteilt.`,
            });
            eventSource.close();
            activeStreamsRef.current.delete(documentId);
          } else if (data.processing_status === 'failed') {
            toast.error('Dokumentverarbeitung fehlgeschlagen', {
              description: data.error_message || 'Ein Fehler ist aufgetreten',
            });
            eventSource.close();
            activeStreamsRef.current.delete(documentId);
          }
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    eventSource.onerror = (_error) => {
      console.log('SSE connection error/closed for document:', documentId);
      eventSource.close();
      activeStreamsRef.current.delete(documentId);

      // Automatic reconnection with exponential backoff
      if (retryCount < 5) {  // Max 5 retries
        const delay = Math.min(1000 * Math.pow(2, retryCount), 30000); // Max 30s
        console.log(`Reconnecting to document ${documentId} in ${delay}ms (attempt ${retryCount + 1}/5)`);

        setTimeout(() => {
          // Check if document is still processing before reconnecting
          queryClient.refetchQueries({ queryKey: ['documents'] }).then(() => {
            const currentData = queryClient.getQueryData(['documents']) as any;
            const currentDoc = currentData?.items?.find((d: any) => d.document_id === documentId);

            if (currentDoc && (currentDoc.processing_status === 'processing' || currentDoc.processing_status === 'uploading')) {
              console.log(`Document ${documentId} still processing, reconnecting...`);
              connectToDocumentStream(documentId, retryCount + 1);
            } else {
              console.log(`Document ${documentId} no longer processing, skipping reconnect`);
            }
          });
        }, delay);
      } else {
        console.error(`Failed to reconnect to document ${documentId} after 5 attempts`);
        toast.error('Verbindung verloren', {
          description: 'Die Verbindung zu den Verarbeitungsupdates wurde unterbrochen. Bitte aktualisieren Sie die Seite.',
        });
      }
    };
  }, [queryClient]);

  // Auto-reconnect to in-progress documents on component mount (handles page refresh)
  useEffect(() => {
    if (documentsData?.items) {
      const processingDocs = documentsData.items.filter(
        (doc) => doc.processing_status === 'processing' || doc.processing_status === 'uploading'
      );

      if (processingDocs.length > 0) {
        console.log(`Found ${processingDocs.length} in-progress documents, auto-reconnecting...`);

        processingDocs.forEach((doc) => {
          console.log(`Auto-reconnecting to document: ${doc.document_id} (${doc.processing_status})`);
          connectToDocumentStream(doc.document_id);
        });
      }
    }
  }, [documentsData?.items, connectToDocumentStream]);

  // Note: Processing documents are no longer in the queue
  // They are removed from queue when processing starts and tracked in documents list
  // SSE reconnection is handled by the useEffect above that watches documentsData

  // Cleanup all SSE connections on component unmount
  useEffect(() => {
    return () => {
      console.log('Cleaning up all SSE connections');
      activeStreamsRef.current.forEach((eventSource, documentId) => {
        console.log('Closing SSE connection for:', documentId);
        eventSource.close();
      });
      activeStreamsRef.current.clear();
    };
  }, []);


  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    onSuccess: () => {
      toast.success('Dokument erfolgreich gelöscht');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error: any) => {
      toast.error('Löschen fehlgeschlagen', {
        description: error.response?.data?.detail || 'Fehler beim Löschen des Dokuments',
      });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      const validFiles: File[] = [];
      const invalidFiles: string[] = [];

      files.forEach((file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        if (ALLOWED_EXTENSIONS.includes(ext)) {
          validFiles.push(file);
        } else {
          invalidFiles.push(file.name);
        }
      });

      if (invalidFiles.length > 0) {
        toast.error('Ungültige Dateitypen übersprungen', {
          description: `${invalidFiles.length} Datei(en) mit ungültigem Typ: ${invalidFiles.slice(0, 3).join(', ')}${invalidFiles.length > 3 ? '...' : ''}`,
        });
      }

      if (validFiles.length > 0) {
        setSelectedFiles((prev) => [...prev, ...validFiles]);
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      const validFiles: File[] = [];
      const invalidFiles: string[] = [];

      files.forEach((file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        if (ALLOWED_EXTENSIONS.includes(ext)) {
          validFiles.push(file);
        } else {
          invalidFiles.push(file.name);
        }
      });

      if (invalidFiles.length > 0) {
        toast.error('Ungültige Dateitypen übersprungen', {
          description: `${invalidFiles.length} Datei(en) mit ungültigem Typ: ${invalidFiles.slice(0, 3).join(', ')}${invalidFiles.length > 3 ? '...' : ''}`,
        });
      }

      if (validFiles.length > 0) {
        setSelectedFiles((prev) => [...prev, ...validFiles]);
      }
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !category) {
      toast.error('Fehlende Informationen', {
        description: 'Bitte wählen Sie mindestens eine Datei und eine Kategorie aus',
      });
      return;
    }

    setIsUploading(true);

    // Upload each file directly - backend adds to queue
    let successCount = 0;
    let failCount = 0;

    for (const file of selectedFiles) {
      try {
        const result = await documentService.uploadDocument(file, category);
        console.log(`[Upload] File added to queue: ${file.name}`, result);
        successCount++;
      } catch (error: any) {
        console.error(`[Upload] Failed to upload ${file.name}:`, error);
        toast.error(`Upload fehlgeschlagen: ${file.name}`, {
          description: error.response?.data?.detail || 'Fehler beim Hochladen',
        });
        failCount++;
      }
    }

    setIsUploading(false);

    // Show summary toast
    if (successCount > 0) {
      toast.success('Dateien zur Warteschlange hinzugefügt', {
        description: `${successCount} Datei(en) werden verarbeitet${failCount > 0 ? `, ${failCount} fehlgeschlagen` : ''}`,
      });
    }

    // Refetch documents list to show newly uploaded items
    queryClient.invalidateQueries({ queryKey: ['documents'] });

    // Clear selected files
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDelete = (documentId: string) => {
    if (confirm('Sind Sie sicher, dass Sie dieses Dokument löschen möchten?')) {
      deleteMutation.mutate(documentId);
    }
  };

  const columns: Column<Document>[] = [
    {
      key: 'filename',
      header: 'Dateiname',
      render: (doc) => (
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium">{doc.filename}</span>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Kategorie',
      render: (doc) => (
        <span className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-sm">
          {translateCategory(doc.category)}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (doc) => (
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            {doc.processing_status === 'completed' ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-green-600">Abgeschlossen</span>
              </>
            ) : doc.processing_status === 'failed' ? (
              <>
                <AlertCircle className="w-4 h-4 text-destructive" />
                <span className="text-destructive">Fehlgeschlagen</span>
              </>
            ) : (
              <>
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-muted-foreground">Wird verarbeitet</span>
              </>
            )}
          </div>
          {doc.processing_step && doc.processing_status === 'processing' && (
            <div className="text-xs text-muted-foreground">
              {doc.processing_step.replace(/_/g, ' ')} ({doc.processing_progress}%)
            </div>
          )}
          {doc.error_message && (
            <div className="text-xs text-destructive" title={doc.error_message}>
              {doc.error_message.substring(0, 50)}{doc.error_message.length > 50 ? '...' : ''}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'upload_date',
      header: 'Hochgeladen',
      render: (doc) => format(new Date(doc.upload_date), 'MMM d, yyyy HH:mm'),
    },
    {
      key: 'uploader_name',
      header: 'Hochgeladen von',
      render: (doc) => doc.uploader_name || '-',
    },
    {
      key: 'actions',
      header: 'Aktionen',
      render: (doc) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleDelete(doc.document_id)}
          disabled={deleteMutation.isPending}
        >
          <Trash2 className="w-4 h-4 text-destructive" />
        </Button>
      ),
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-destructive" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Wartend';
      case 'processing':
        return 'Wird verarbeitet';
      case 'completed':
        return 'Abgeschlossen';
      case 'failed':
        return 'Fehlgeschlagen';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Dokument hochladen</CardTitle>
          <CardDescription>
            Laden Sie Dokumente in die Pinecone-Vektordatenbank für KI-gestützte Suche hoch
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag and Drop Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-lg font-medium mb-2">
              {selectedFiles.length > 0
                ? `${selectedFiles.length} Datei(en) ausgewählt`
                : 'Dateien hierher ziehen und ablegen'}
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              oder klicken zum Durchsuchen (mehrere Dateien möglich)
            </p>
            <Input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept={ALLOWED_EXTENSIONS.join(',')}
              className="hidden"
              id="file-upload"
              multiple
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              Dateien auswählen
            </Button>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <Label>Ausgewählte Dateien ({selectedFiles.length})</Label>
              <div className="border rounded-lg divide-y max-h-40 overflow-y-auto">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 hover:bg-muted/50">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-sm truncate">{file.name}</span>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveFile(index)}
                      disabled={isUploading}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Category Selection */}
          <div className="space-y-2">
            <Label htmlFor="category">Kategorie</Label>
            <Select value={category} onValueChange={setCategory} disabled={isUploading}>
              <SelectTrigger id="category">
                <SelectValue placeholder="Kategorie auswählen" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="manuals">Handbücher</SelectItem>
                <SelectItem value="specifications">Spezifikationen</SelectItem>
                <SelectItem value="guides">Anleitungen</SelectItem>
                <SelectItem value="reports">Berichte</SelectItem>
                <SelectItem value="other">Sonstiges</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || !category}
            className="w-full"
          >
            <Upload className="w-4 h-4 mr-2" />
            {selectedFiles.length > 0
              ? `${selectedFiles.length} Dokument(e) zur Warteschlange hinzufügen`
              : 'Dokumente hochladen'}
          </Button>

          <p className="text-xs text-muted-foreground">
            Erlaubte Dateitypen: {ALLOWED_EXTENSIONS.join(', ')}
          </p>
        </CardContent>
      </Card>

      {/* Upload Queue - Only shows pending items waiting to be processed */}
      {serverQueue.queue.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Upload-Warteschlange</CardTitle>
                <CardDescription>
                  {serverQueue.stats.pending} Dokument(e) warten auf Verarbeitung
                  {serverQueue.stats.processing > 0 && ` • ${serverQueue.stats.processing} wird gerade verarbeitet`}
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (confirm('Möchten Sie alle Elemente aus der Warteschlange entfernen? Dies kann nicht rückgängig gemacht werden.')) {
                    serverQueue.clearQueue();
                  }
                }}
                disabled={serverQueue.isClearing}
              >
                Alle löschen
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {serverQueue.queue.map((item) => (
                <div
                  key={item.queue_id}
                  className="flex items-center gap-3 p-3 border rounded-lg bg-card"
                >
                  <div className="flex-shrink-0">
                    {getStatusIcon(item.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium truncate">{item.filename}</span>
                      <span className="text-xs px-2 py-0.5 bg-secondary text-secondary-foreground rounded">
                        {translateCategory(item.category)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Position: {item.position}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{getStatusText(item.status)}</span>
                      <span>•</span>
                      <span>{(item.file_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                      <span>•</span>
                      <span>von {item.uploader_name}</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => serverQueue.removeFromQueue(item.queue_id)}
                    disabled={serverQueue.isRemoving}
                    title="Aus Warteschlange entfernen und Dokument löschen"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>Hochgeladene Dokumente</CardTitle>
          <CardDescription>
            Verwalten Sie Dokumente, die in die Vektordatenbank hochgeladen wurden
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={documentsData?.items || []}
            columns={columns}
            loading={isLoading}
            emptyTitle="Keine Dokumente gefunden"
            emptyMessage="Laden Sie Ihr erstes Dokument hoch, um zu beginnen."
          />
        </CardContent>
      </Card>
    </div>
  );
}
