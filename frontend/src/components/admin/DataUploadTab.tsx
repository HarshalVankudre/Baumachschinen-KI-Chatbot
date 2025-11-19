import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, Trash2, X, CheckCircle, AlertCircle, FileJson, Settings } from 'lucide-react';
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
import apiClient from '@/services/api';
import { toast } from 'sonner';
import type { Document, UploadType, ProcessingStage, MachineryUploadResponse } from '@/types';
import { format } from 'date-fns';
import { translateCategory } from '@/utils/translations';

// Constants
const DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.ppt', '.jpg', '.jpeg', '.png', '.gif'];
const MACHINERY_EXTENSIONS = ['.json'];
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;
const OPTIMISTIC_UPDATE_DELAY_MS = 300;

// Processing stages for visual feedback
const PROCESSING_STAGES: ProcessingStage[] = [
  { key: 'parsing', label: 'Daten werden analysiert...', icon: 'file' },
  { key: 'embeddings', label: 'Embeddings werden generiert...', icon: 'brain' },
  { key: 'vectors', label: 'Vektoren werden gespeichert...', icon: 'database' },
  { key: 'graph', label: 'Wissensgraph wird erstellt...', icon: 'network' },
];

export function DataUploadTab() {
  const [uploadType, setUploadType] = useState<UploadType>('documents');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('manuals');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [currentStage, setCurrentStage] = useState<number>(0);
  const [machineryStats, setMachineryStats] = useState<MachineryUploadResponse | null>(null);
  const [jsonPreview, setJsonPreview] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documentsData, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentService.getDocuments(),
  });

  // Store active SSE connections
  const activeStreamsRef = useRef<Map<string, EventSource>>(new Map());

  // Connect to SSE stream for real-time processing updates
  const connectToDocumentStream = useCallback((documentId: string, retryCount = 0) => {
    if (activeStreamsRef.current.has(documentId)) {
      console.log('Already connected to document stream:', documentId);
      return;
    }

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/documents/stream/${documentId}`,
      { withCredentials: true }
    );

    activeStreamsRef.current.set(documentId, eventSource);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

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
          console.log('Document status update:', data.processing_status);
          queryClient.refetchQueries({ queryKey: ['documents'] });

          // Update stage indicator based on progress
          if (data.processing_progress) {
            const stageIndex = Math.floor((data.processing_progress / 100) * PROCESSING_STAGES.length);
            setCurrentStage(Math.min(stageIndex, PROCESSING_STAGES.length - 1));
          }

          if (data.processing_status === 'completed') {
            toast.success('Daten erfolgreich verarbeitet', {
              description: `Die Datei wurde in ${data.chunk_count || 0} Abschnitte aufgeteilt.`,
            });
            eventSource.close();
            activeStreamsRef.current.delete(documentId);
            setCurrentStage(0);
          } else if (data.processing_status === 'failed') {
            toast.error('Verarbeitung fehlgeschlagen', {
              description: data.error_message || 'Ein Fehler ist aufgetreten',
            });
            eventSource.close();
            activeStreamsRef.current.delete(documentId);
            setCurrentStage(0);
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

      if (retryCount < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          BASE_RECONNECT_DELAY_MS * Math.pow(2, retryCount),
          MAX_RECONNECT_DELAY_MS
        );
        console.log(
          `Reconnecting to document ${documentId} in ${delay}ms ` +
          `(attempt ${retryCount + 1}/${MAX_RECONNECT_ATTEMPTS})`
        );

        setTimeout(() => {
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
          description: 'Die Verbindung zu den Verarbeitungsupdates wurde unterbrochen. Bitte laden Sie die Seite neu.',
        });
      }
    };
  }, [queryClient]);

  // Auto-reconnect to in-progress documents
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

  // Cleanup SSE connections
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
      if (!selectedFile) {
        throw new Error('Bitte wählen Sie eine Datei zum Hochladen aus');
      }

      // Both documents and machinery JSON use the same upload endpoint
      // The backend routes JSON files to the JSON processor automatically
      if (uploadType === 'machinery') {
        // For machinery JSON, use 'machinery' category
        return documentService.uploadDocument(selectedFile, 'machinery');
      } else {
        // For documents, use the selected category
        if (!category) {
          throw new Error('Bitte wählen Sie eine Kategorie aus');
        }
        return documentService.uploadDocument(selectedFile, category);
      }
    },
    onSuccess: async (response: any) => {
      if (uploadType === 'machinery') {
        // Show success message for JSON machinery data
        toast.success('JSON-Maschinendaten erfolgreich hochgeladen', {
          description: `${response.properties_extracted || 0} Eigenschaften extrahiert, ${response.properties_uploaded || 0} hochgeladen. Daten sind für alle Benutzer verfügbar.`,
        });

        // Connect to SSE for real-time processing updates
        const documentId = response.document_id;
        if (documentId) {
          setTimeout(() => connectToDocumentStream(documentId), OPTIMISTIC_UPDATE_DELAY_MS);
        }
      } else {
        toast.success('Dokument erfolgreich hochgeladen', {
          description: 'Das Dokument wird im Hintergrund verarbeitet.',
        });

        const documentId = response.document_id;

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

        await new Promise(resolve => setTimeout(resolve, OPTIMISTIC_UPDATE_DELAY_MS));
        await queryClient.refetchQueries({ queryKey: ['documents'] });

        if (documentId) {
          connectToDocumentStream(documentId);
        }
      }

      // Reset form
      setSelectedFile(null);
      setUploadProgress(0);
      setJsonPreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    onError: (error: any) => {
      toast.error('Upload fehlgeschlagen', {
        description: error.response?.data?.detail || error.message || 'Fehler beim Hochladen der Datei',
      });
    },
    onSettled: () => {
      setIsUploading(false);
      setCurrentStage(0);
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
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = uploadType === 'machinery' ? MACHINERY_EXTENSIONS : DOCUMENT_EXTENSIONS;

    if (!allowedExtensions.includes(ext)) {
      toast.error('Ungültiger Dateityp', {
        description: `Erlaubte Typen: ${allowedExtensions.join(', ')}`,
      });
      return;
    }

    setSelectedFile(file);

    // Preview JSON files
    if (uploadType === 'machinery' && ext === '.json') {
      try {
        const text = await file.text();
        const json = JSON.parse(text);
        setJsonPreview(json);
      } catch (error) {
        toast.error('Ungültige JSON-Datei', {
          description: 'Die ausgewählte Datei enthält kein gültiges JSON',
        });
        setSelectedFile(null);
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

    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Keine Datei ausgewählt', {
        description: 'Bitte wählen Sie eine Datei zum Hochladen aus',
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

  const handleTypeChange = (type: UploadType) => {
    setUploadType(type);
    setSelectedFile(null);
    setJsonPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
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
                <span className="text-muted-foreground">In Verarbeitung</span>
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
      render: (doc) => format(new Date(doc.upload_date), 'dd.MM.yyyy HH:mm'),
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

  const allowedExtensions = uploadType === 'machinery' ? MACHINERY_EXTENSIONS : DOCUMENT_EXTENSIONS;

  return (
    <div className="space-y-8">
      {/* Type Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card
          className={`cursor-pointer transition-all duration-300 hover-lift border-2 ${
            uploadType === 'documents'
              ? 'border-blue-500 shadow-premium-lg shadow-blue-500/20 scale-[1.02]'
              : 'border-border/50 hover:border-blue-300'
          }`}
          onClick={() => handleTypeChange('documents')}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-xl transition-all duration-300 ${
                uploadType === 'documents'
                  ? 'bg-blue-500 text-white shadow-premium-md'
                  : 'bg-blue-50 text-blue-600 dark:bg-blue-950/30'
              }`}>
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg">Dokumente hochladen</CardTitle>
                <CardDescription className="text-xs mt-1">
                  PDF, DOC, Bilder
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pb-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className={`h-2 w-2 rounded-full ${uploadType === 'documents' ? 'bg-blue-500 animate-pulse' : 'bg-border'}`} />
              <span>Wissensdatenbank</span>
            </div>
          </CardContent>
        </Card>

        <Card
          className={`cursor-pointer transition-all duration-300 hover-lift border-2 ${
            uploadType === 'machinery'
              ? 'border-orange-500 shadow-premium-lg shadow-orange-500/20 scale-[1.02]'
              : 'border-border/50 hover:border-orange-300'
          }`}
          onClick={() => handleTypeChange('machinery')}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-xl transition-all duration-300 ${
                uploadType === 'machinery'
                  ? 'bg-orange-500 text-white shadow-premium-md'
                  : 'bg-orange-50 text-orange-600 dark:bg-orange-950/30'
              }`}>
                <Settings className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg">Maschinendaten hochladen</CardTitle>
                <CardDescription className="text-xs mt-1">
                  JSON-Spezifikationen
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pb-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className={`h-2 w-2 rounded-full ${uploadType === 'machinery' ? 'bg-orange-500 animate-pulse' : 'bg-border'}`} />
              <span>Gerätekatalog</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upload Section */}
      <Card className="overflow-hidden">
        <div className={`h-1 w-full transition-all duration-500 ${
          uploadType === 'documents'
            ? 'bg-gradient-to-r from-blue-500 to-blue-600'
            : 'bg-gradient-to-r from-orange-500 to-orange-600'
        }`} />
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {uploadType === 'documents' ? (
              <FileText className="w-5 h-5 text-blue-500" />
            ) : (
              <Settings className="w-5 h-5 text-orange-500" />
            )}
            {uploadType === 'documents' ? 'Dokumente' : 'Maschinendaten'} hochladen
          </CardTitle>
          <CardDescription>
            {uploadType === 'documents'
              ? 'Laden Sie Dokumente in die Pinecone-Vektordatenbank für KI-gestützte Suche hoch'
              : 'Laden Sie JSON-Maschinendaten für die Wissensgraph-Integration hoch'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Category Selection - Only for documents */}
          {uploadType === 'documents' && (
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
                  <SelectItem value="other">Sonstige</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Drag and Drop Area */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
              dragActive
                ? uploadType === 'documents'
                  ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[1.01]'
                  : 'border-orange-500 bg-orange-50/50 dark:bg-orange-950/20 scale-[1.01]'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50 hover:bg-muted/20'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className={`w-32 h-32 rounded-full transition-all duration-500 ${
                dragActive
                  ? uploadType === 'documents'
                    ? 'bg-blue-500/10 scale-150'
                    : 'bg-orange-500/10 scale-150'
                  : 'bg-transparent scale-100'
              }`} />
            </div>

            <div className="relative z-10">
              {uploadType === 'documents' ? (
                <Upload className={`w-16 h-16 mx-auto mb-4 transition-all duration-300 ${
                  dragActive ? 'text-blue-500 scale-110' : 'text-muted-foreground'
                }`} />
              ) : (
                <FileJson className={`w-16 h-16 mx-auto mb-4 transition-all duration-300 ${
                  dragActive ? 'text-orange-500 scale-110' : 'text-muted-foreground'
                }`} />
              )}

              <p className="text-xl font-semibold mb-2">
                {selectedFile ? selectedFile.name : 'Datei hierher ziehen oder klicken'}
              </p>
              <p className="text-sm text-muted-foreground mb-6">
                zum Durchsuchen
              </p>

              <Input
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                accept={allowedExtensions.join(',')}
                className="hidden"
                id="file-upload"
              />

              <div className="flex items-center justify-center gap-3">
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className={uploadType === 'documents'
                    ? 'border-blue-500/50 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/20'
                    : 'border-orange-500/50 hover:border-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950/20'
                  }
                >
                  Datei auswählen
                </Button>
                {selectedFile && (
                  <Button
                    variant="ghost"
                    size="lg"
                    onClick={() => {
                      setSelectedFile(null);
                      setJsonPreview(null);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                      }
                    }}
                  >
                    <X className="w-5 h-5" />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* JSON Preview */}
          {jsonPreview && uploadType === 'machinery' && (
            <Card className="bg-muted/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileJson className="w-4 h-4 text-orange-500" />
                  JSON-Vorschau
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-background p-4 rounded-lg overflow-auto max-h-48 scrollbar-thin">
                  {JSON.stringify(jsonPreview, null, 2)}
                </pre>
                <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
                  {Array.isArray(jsonPreview) && (
                    <div>Einträge: <span className="font-semibold text-orange-500">{jsonPreview.length}</span></div>
                  )}
                  {typeof jsonPreview === 'object' && (
                    <div>Schlüssel: <span className="font-semibold text-orange-500">{Object.keys(jsonPreview).length}</span></div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Upload Progress with Stages */}
          {isUploading && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium">
                  <span>Wird hochgeladen...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress
                  value={uploadProgress}
                  className={`h-3 ${
                    uploadType === 'documents'
                      ? '[&>div]:bg-gradient-to-r [&>div]:from-blue-500 [&>div]:to-blue-600'
                      : '[&>div]:bg-gradient-to-r [&>div]:from-orange-500 [&>div]:to-orange-600'
                  }`}
                />
              </div>

              {/* Processing Stages */}
              {uploadProgress === 100 && (
                <div className="space-y-3 pt-2">
                  <p className="text-sm font-medium text-muted-foreground">Verarbeitungsschritte:</p>
                  <div className="grid grid-cols-2 gap-3">
                    {PROCESSING_STAGES.map((stage, index) => (
                      <div
                        key={stage.key}
                        className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                          index < currentStage
                            ? uploadType === 'documents'
                              ? 'bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800'
                              : 'bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800'
                            : index === currentStage
                            ? uploadType === 'documents'
                              ? 'bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500'
                              : 'bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-500'
                            : 'bg-muted/30 border border-border/50'
                        }`}
                      >
                        {index < currentStage ? (
                          <CheckCircle className={`w-4 h-4 ${
                            uploadType === 'documents' ? 'text-blue-500' : 'text-orange-500'
                          }`} />
                        ) : index === currentStage ? (
                          <div className={`w-4 h-4 border-2 border-t-transparent rounded-full animate-spin ${
                            uploadType === 'documents' ? 'border-blue-500' : 'border-orange-500'
                          }`} />
                        ) : (
                          <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />
                        )}
                        <span className={`text-sm font-medium ${
                          index <= currentStage ? 'text-foreground' : 'text-muted-foreground'
                        }`}>
                          {stage.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Machinery Upload Stats */}
          {machineryStats && uploadType === 'machinery' && (
            <Card className="bg-gradient-to-br from-orange-50 to-orange-100/50 dark:from-orange-950/20 dark:to-orange-900/10 border-orange-200 dark:border-orange-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-orange-500" />
                  Upload-Zusammenfassung
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-background/60 rounded-lg p-4">
                    <div className="text-2xl font-bold text-orange-500">{machineryStats.machines_added || 0}</div>
                    <div className="text-xs text-muted-foreground mt-1">Maschinen hinzugefügt</div>
                  </div>
                  <div className="bg-background/60 rounded-lg p-4">
                    <div className="text-2xl font-bold text-orange-500">{machineryStats.relationships_created || 0}</div>
                    <div className="text-xs text-muted-foreground mt-1">Beziehungen erstellt</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            size="lg"
            className={`w-full font-semibold ${
              uploadType === 'documents'
                ? 'bg-blue-500 hover:bg-blue-600 shadow-premium-md hover:shadow-premium-lg shadow-blue-500/20'
                : 'bg-orange-500 hover:bg-orange-600 shadow-premium-md hover:shadow-premium-lg shadow-orange-500/20'
            }`}
          >
            <Upload className="w-5 h-5 mr-2" />
            {isUploading ? 'Wird hochgeladen...' : `${uploadType === 'documents' ? 'Dokument' : 'Maschinendaten'} hochladen`}
          </Button>

          <p className="text-xs text-muted-foreground text-center">
            Erlaubte Dateitypen: {allowedExtensions.join(', ')} • Max. Größe: 50 MB
          </p>
        </CardContent>
      </Card>

      {/* Documents List - Only show for documents type */}
      {uploadType === 'documents' && (
        <Card>
          <CardHeader>
            <CardTitle>Hochgeladene Dokumente</CardTitle>
            <CardDescription>
              Verwalten Sie die in die Vektordatenbank hochgeladenen Dokumente
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
      )}
    </div>
  );
}
