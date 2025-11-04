import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { documentService } from '@/services/documentService';
import { toast } from 'sonner';
import { Upload, FileText, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getCategoryOptions } from '@/utils/translations';

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

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  abortController: AbortController;
}

export function DocumentUpload() {
  const queryClient = useQueryClient();

  const [selectedCategory, setSelectedCategory] = useState('manuals');
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const validateFile = (file: File): string | null => {
    const allowedTypes = Object.keys(ACCEPTED_TYPES);

    if (!allowedTypes.includes(file.type)) {
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

    // Limit to 5 files at a time
    if (validFiles.length > 5) {
      toast.error('Maximum 5 files at once. Only the first 5 will be uploaded.');
    }

    const filesToUpload = validFiles.slice(0, 5);

    // Queue files if there are already uploads in progress
    const queuedFiles = filesToUpload.map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      progress: 0,
      abortController: new AbortController(),
    }));

    setUploadingFiles((prev) => [...prev, ...queuedFiles]);

    // Upload files sequentially if more than 5 total
    for (const uploadingFile of queuedFiles) {
      try {
        const _response = await documentService.uploadDocument(
          uploadingFile.file,
          selectedCategory,
          (progress) => {
            setUploadingFiles((prev) =>
              prev.map((f) =>
                f.id === uploadingFile.id ? { ...f, progress } : f
              )
            );
          }
        );

        toast.success(`${uploadingFile.file.name} uploaded successfully. Processing...`);

        // Remove from uploading list
        setUploadingFiles((prev) => prev.filter((f) => f.id !== uploadingFile.id));

        // Wait for backend to commit to database before refetching
        await new Promise(resolve => setTimeout(resolve, 300));

        // Refresh documents list with refetch instead of invalidate to ensure immediate update
        await queryClient.refetchQueries({ queryKey: ['documents'] });
      } catch (error: any) {
        const errorMessage = error?.response?.data?.message || 'Upload failed';
        toast.error(`${uploadingFile.file.name}: ${errorMessage}`);

        // Remove from uploading list
        setUploadingFiles((prev) => prev.filter((f) => f.id !== uploadingFile.id));
      }
    }
  };

  const handleCancelUpload = (fileId: string) => {
    const file = uploadingFiles.find((f) => f.id === fileId);
    if (file) {
      file.abortController.abort();
      setUploadingFiles((prev) => prev.filter((f) => f.id !== fileId));
      toast.info(`Cancelled upload of ${file.file.name}`);
    }
  };

  const handleBrowseFiles = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = Object.values(ACCEPTED_TYPES).flat().join(',');
    input.onchange = (e: any) => {
      const files = Array.from(e.target.files) as File[];
      handleFileUpload(files);
    };
    input.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
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
          >
            Browse Files
          </Button>
        </div>

        {/* Upload Progress */}
        {uploadingFiles.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-semibold">Uploading Files:</h3>
            {uploadingFiles.map((uploadingFile) => (
              <div
                key={uploadingFile.id}
                className="flex items-center gap-3 p-3 border rounded-lg bg-card"
              >
                <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-medium truncate">
                      {uploadingFile.file.name}
                    </div>
                    <div className="text-xs text-muted-foreground ml-2">
                      {formatFileSize(uploadingFile.file.size)}
                    </div>
                  </div>
                  <Progress value={uploadingFile.progress} className="h-2" />
                </div>
                <div className="text-sm text-muted-foreground font-medium w-12 text-right">
                  {uploadingFile.progress}%
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCancelUpload(uploadingFile.id);
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
