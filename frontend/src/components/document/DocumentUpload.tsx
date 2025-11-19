import { useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { documentService } from '@/services/documentService';
import { toast } from 'sonner';
import { Upload, FileText, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getCategoryOptions } from '@/utils/translations';
import type { Document } from '@/types';

const CATEGORIES = getCategoryOptions();

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.ms-powerpoint': ['.ppt'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/gif': ['.gif'],
};

interface ProcessingDocument {
  id: string;
  filename: string;
  size: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  processing_step?: string;
  processing_progress?: number;
  error_message?: string;
}

export function DocumentUpload() {
  const queryClient = useQueryClient();

  const [selectedCategory, setSelectedCategory] = useState('manuals');
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [processingDocs, setProcessingDocs] = useState<ProcessingDocument[]>([]);

  const validateFile = (file: File): string | null => {
    const allowedTypes = Object.keys(ACCEPTED_TYPES);
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    // Check if file type matches OR if extension is allowed
    // (Some browsers don't set MIME type correctly)
    const isTypeAllowed = allowedTypes.includes(file.type);
    const isExtensionAllowed = Object.values(ACCEPTED_TYPES)
      .flat()
      .includes(fileExtension);

    if (!isTypeAllowed && !isExtensionAllowed) {
      return `File type not supported: ${file.name}. Please upload PDF, DOCX, PPT, XLS, or image files.`;
    }

    return null;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = Array.from(e.dataTransfer.files);
      await handleFileUpload(files);
    },
    [selectedCategory]
  );

  const handleFileUpload = async (files: File[]) => {
    if (!selectedCategory) {
      toast.error('Please select a category first');
      return;
    }

    if (isUploading) {
      toast.error('Upload already in progress. Please wait...');
      return;
    }

    const validFiles: File[] = [];

    // Validate files
    for (const file of files) {
      const error = validateFile(file);
      if (error) {
        toast.error(error);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) {
      return;
    }

    // Limit to 10 files at a time
    if (validFiles.length > 10) {
      toast.error('Maximum 10 files at once. Only the first 10 will be uploaded.');
    }

    const filesToUpload = validFiles.slice(0, 10);
    setIsUploading(true);

    // Create initial processing docs with uploading status
    const initialDocs: ProcessingDocument[] = filesToUpload.map((file) => ({
      id: `temp-${Date.now()}-${Math.random()}`,
      filename: file.name,
      size: file.size,
      status: 'uploading',
    }));

    setProcessingDocs(initialDocs);

    // Upload all files in parallel
    const uploadPromises = filesToUpload.map(async (file, index) => {
      const tempId = initialDocs[index].id;

      try {
        const response = await documentService.uploadDocument(file, selectedCategory);

        // Update with document ID from server
        setProcessingDocs((prev) =>
          prev.map((doc) =>
            doc.id === tempId
              ? {
                  ...doc,
                  id: response.document_id,
                  status: response.status || 'processing',
                }
              : doc
          )
        );

        // Subscribe to SSE updates for this document
        const cleanup = documentService.subscribeToDocumentUpdates(
          response.document_id,
          (data) => {
            console.log(`[Upload SSE] Update for ${file.name}:`, data);

            if (data.type === 'connected' || data.type === 'done') {
              return;
            }

            // Update processing doc status
            setProcessingDocs((prev) =>
              prev.map((doc) =>
                doc.id === response.document_id
                  ? {
                      ...doc,
                      status: data.processing_status || doc.status,
                      processing_step: data.processing_step,
                      processing_progress: data.processing_progress,
                      error_message: data.error_message,
                    }
                  : doc
              )
            );

            // If completed or failed, refresh documents list and remove from processing
            if (data.processing_status === 'completed' || data.processing_status === 'failed') {
              setTimeout(() => {
                setProcessingDocs((prev) => prev.filter((doc) => doc.id !== response.document_id));
                queryClient.refetchQueries({ queryKey: ['documents'] });
              }, 2000); // Keep showing for 2 seconds before removing
            }
          }
        );

        // Immediately refetch to show the document in the list
        await queryClient.refetchQueries({ queryKey: ['documents'] });

        return { success: true, filename: file.name };
      } catch (error: any) {
        const errorMessage = error?.response?.data?.message || 'Upload failed';

        // Update status to failed
        setProcessingDocs((prev) =>
          prev.map((doc) =>
            doc.id === tempId
              ? {
                  ...doc,
                  status: 'failed',
                  error_message: errorMessage,
                }
              : doc
          )
        );

        // Remove after showing error for 5 seconds
        setTimeout(() => {
          setProcessingDocs((prev) => prev.filter((doc) => doc.id !== tempId));
        }, 5000);

        return { success: false, filename: file.name, error: errorMessage };
      }
    });

    // Wait for all uploads to complete
    const results = await Promise.all(uploadPromises);

    const successCount = results.filter((r) => r.success).length;
    const failCount = results.filter((r) => !r.success).length;

    if (successCount > 0) {
      toast.success(`${successCount} file(s) uploaded successfully. Processing in background...`);
    }
    if (failCount > 0) {
      toast.error(`${failCount} file(s) failed to upload`);
    }

    setIsUploading(false);
  };

  const handleBrowseFiles = () => {
    // Trigger the hidden file input
    const fileInput = document.getElementById('file-upload-input') as HTMLInputElement;
    if (fileInput) {
      fileInput.click();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileUpload(files);
      // Reset input so same files can be selected again
      e.target.value = '';
    }
  };

  return (
    <>
      {/* Hidden file input for multiple file selection */}
      <input
        id="file-upload-input"
        type="file"
        multiple={true}
        accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.gif"
        onChange={handleFileInputChange}
        className="hidden"
      />

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Add documents to the knowledge base for the AI chatbot to reference
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            'p-12 rounded-lg border-2 border-dashed transition-all duration-200 cursor-pointer',
            dragActive
              ? 'bg-primary/10 border-primary'
              : 'bg-muted/50 border-muted-foreground/20 hover:border-muted-foreground/40'
          )}
          onClick={handleBrowseFiles}
        >
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="rounded-full bg-primary/10 p-6">
              <Upload className="h-12 w-12 text-primary" />
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2">
                Drag and drop files here, or click to browse
              </h3>
              <p className="text-sm text-muted-foreground">
                Select <strong>multiple files</strong> at once (up to 10)
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Supports: PDF, DOCX, PPT, PPTX, XLS, XLSX, PNG, JPG, JPEG, GIF
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium mb-2 block">
              Category <span className="text-destructive">*</span>
            </label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            variant="default"
            onClick={handleBrowseFiles}
            className="mt-6"
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : 'Browse Files'}
          </Button>
        </div>

        {/* Processing Documents - Real-time Status */}
        {processingDocs.length > 0 && (
          <div className="space-y-3 mt-6">
            <h3 className="font-semibold">Processing Documents:</h3>
            {processingDocs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-3 border rounded-lg bg-card"
              >
                {/* Status Icon */}
                {doc.status === 'uploading' && (
                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin shrink-0" />
                )}
                {doc.status === 'processing' && (
                  <Loader2 className="h-5 w-5 text-orange-600 animate-spin shrink-0" />
                )}
                {doc.status === 'completed' && (
                  <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                )}
                {doc.status === 'failed' && (
                  <XCircle className="h-5 w-5 text-red-600 shrink-0" />
                )}

                {/* Document Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-medium truncate">
                      {doc.filename}
                    </div>
                    <div className="text-xs text-muted-foreground ml-2">
                      {(doc.size / 1024).toFixed(0)} KB
                    </div>
                  </div>

                  {/* Status Text */}
                  <div className="text-xs text-muted-foreground">
                    {doc.status === 'uploading' && 'Uploading...'}
                    {doc.status === 'processing' && (
                      <span>
                        {doc.processing_step?.replace(/_/g, ' ') || 'Processing...'}
                      </span>
                    )}
                    {doc.status === 'completed' && 'Completed'}
                    {doc.status === 'failed' && (
                      <span className="text-red-600">
                        Failed: {doc.error_message || 'Unknown error'}
                      </span>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {(doc.status === 'processing' || doc.status === 'uploading') &&
                    doc.processing_progress !== null &&
                    doc.processing_progress !== undefined && (
                      <div className="mt-2">
                        <Progress value={doc.processing_progress} className="h-1.5" />
                      </div>
                    )}
                </div>

                {/* Status Badge */}
                <div
                  className={cn(
                    'px-2 py-1 rounded-full text-xs font-medium shrink-0',
                    doc.status === 'uploading' &&
                      'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                    doc.status === 'processing' &&
                      'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
                    doc.status === 'completed' &&
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                    doc.status === 'failed' &&
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                  )}
                >
                  {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                  {doc.processing_progress !== null &&
                    doc.processing_progress !== undefined &&
                    (doc.status === 'processing' || doc.status === 'uploading') &&
                    ` ${doc.processing_progress}%`}
                </div>
              </div>
            ))}
          </div>
        )}
        </CardContent>
      </Card>
    </>
  );
}
