import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, Trash2, X, CheckCircle, AlertCircle } from 'lucide-react';
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documentsData, isLoading, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentService.getDocuments(),
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
      `http://localhost:8000/api/documents/stream/${documentId}`,
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

    eventSource.onerror = (error) => {
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

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile || !category) {
        throw new Error('Bitte wählen Sie eine Datei und Kategorie aus');
      }
      return documentService.uploadDocument(selectedFile, category, setUploadProgress);
    },
    onSuccess: async (response: any) => {
      toast.success('Dokument erfolgreich hochgeladen', {
        description: 'Das Dokument wird im Hintergrund verarbeitet.',
      });

      const documentId = response.document_id;

      // Optimistic update: add document to cache immediately
      if (documentId && selectedFile) {
        queryClient.setQueryData(['documents'], (oldData: any) => {
          if (!oldData) return oldData;

          const newDocument = {
            document_id: documentId,
            filename: response.filename || selectedFile.name,
            category: category,
            upload_date: new Date().toISOString(),
            uploader_name: response.uploader_name || '-',
            uploader_id: response.uploader_id || '',
            file_size_bytes: selectedFile.size,
            processing_status: 'uploading' as const,
            chunk_count: null,
            error_message: null,
          };

          return {
            ...oldData,
            items: [newDocument, ...(oldData.items || [])],
            total: (oldData.total || 0) + 1,
          };
        });
      }

      // Wait a bit for backend to commit to database, then refetch
      await new Promise(resolve => setTimeout(resolve, 300));
      await queryClient.refetchQueries({ queryKey: ['documents'] });

      // Connect to SSE for real-time processing updates
      if (documentId) {
        connectToDocumentStream(documentId);
      }

      // Reset form
      setSelectedFile(null);
      setCategory('');
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    onError: (error: any) => {
      toast.error('Upload fehlgeschlagen', {
        description: error.response?.data?.detail || 'Fehler beim Hochladen des Dokuments',
      });
    },
    onSettled: () => {
      setIsUploading(false);
    },
  });

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
    const file = e.target.files?.[0];
    if (file) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        toast.error('Ungültiger Dateityp', {
          description: `Erlaubte Typen: ${ALLOWED_EXTENSIONS.join(', ')}`,
        });
        return;
      }
      setSelectedFile(file);
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

    const file = e.dataTransfer.files?.[0];
    if (file) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        toast.error('Ungültiger Dateityp', {
          description: `Erlaubte Typen: ${ALLOWED_EXTENSIONS.join(', ')}`,
        });
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !category) {
      toast.error('Fehlende Informationen', {
        description: 'Bitte wählen Sie eine Datei und Kategorie aus',
      });
      return;
    }
    setIsUploading(true);
    uploadMutation.mutate();
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
              {selectedFile ? selectedFile.name : 'Datei hierher ziehen und ablegen'}
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              oder klicken zum Durchsuchen
            </p>
            <Input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept={ALLOWED_EXTENSIONS.join(',')}
              className="hidden"
              id="file-upload"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              Datei auswählen
            </Button>
            {selectedFile && (
              <Button
                variant="ghost"
                size="sm"
                className="ml-2"
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>

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

          {/* Upload Progress */}
          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Wird hochgeladen...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !category || isUploading}
            className="w-full"
          >
            <Upload className="w-4 h-4 mr-2" />
            {isUploading ? 'Wird hochgeladen...' : 'Dokument hochladen'}
          </Button>

          <p className="text-xs text-muted-foreground">
            Erlaubte Dateitypen: {ALLOWED_EXTENSIONS.join(', ')}
          </p>
        </CardContent>
      </Card>

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
