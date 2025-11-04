import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { DataTable, type Column } from '@/components/shared/DataTable';
import { SearchInput } from '@/components/shared/SearchInput';
import { useDebounce } from '@/hooks/useDebounce';
import { documentService } from '@/services/documentService';
import { toast } from 'sonner';
import { Loader2, CheckCircle2, XCircle, AlertCircle, Trash2 } from 'lucide-react';
import type { Document } from '@/types';
import { translateCategory, getCategoryOptions } from '@/utils/translations';

const CATEGORIES = getCategoryOptions();

type DateRangePreset = 'all' | 'today' | 'last7' | 'last30';

interface DeleteDialogState {
  open: boolean;
  document: Document | null;
}

export function DocumentList() {
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [uploaderFilter, setUploaderFilter] = useState<string>('all');
  const [dateRangePreset, setDateRangePreset] = useState<DateRangePreset>('all');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(search, 300);

  const [deleteDialog, setDeleteDialog] = useState<DeleteDialogState>({
    open: false,
    document: null,
  });

  // Calculate date range based on preset
  useEffect(() => {
    const now = new Date();
    let start = '';
    let end = '';

    switch (dateRangePreset) {
      case 'today':
        start = format(startOfDay(now), "yyyy-MM-dd'T'HH:mm:ss");
        end = format(endOfDay(now), "yyyy-MM-dd'T'HH:mm:ss");
        break;
      case 'last7':
        start = format(startOfDay(subDays(now, 7)), "yyyy-MM-dd'T'HH:mm:ss");
        end = format(endOfDay(now), "yyyy-MM-dd'T'HH:mm:ss");
        break;
      case 'last30':
        start = format(startOfDay(subDays(now, 30)), "yyyy-MM-dd'T'HH:mm:ss");
        end = format(endOfDay(now), "yyyy-MM-dd'T'HH:mm:ss");
        break;
      case 'all':
        start = '';
        end = '';
        break;
    }

    setStartDate(start);
    setEndDate(end);
    setPage(1);
  }, [dateRangePreset]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, categoryFilter, uploaderFilter]);

  // Fetch documents
  const { data: documentsData, isLoading, error } = useQuery({
    queryKey: [
      'documents',
      debouncedSearch,
      categoryFilter,
      uploaderFilter,
      startDate,
      endDate,
      page,
    ],
    queryFn: () =>
      documentService.getDocuments({
        search: debouncedSearch || undefined,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        uploaded_by: uploaderFilter !== 'all' ? uploaderFilter : undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
      }),
    retry: (failureCount, error: any) => {
      // Don't retry on authentication or authorization errors
      if (error?.message?.includes('Authentication required') ||
          error?.message?.includes('permission')) {
        return false;
      }
      // Retry up to 2 times for other errors
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
  });

  // Get unique uploaders for filter
  const uploaders = [
    ...new Set(documentsData?.items?.map((doc) => doc.uploader_name).filter(Boolean) || []),
  ];

  // Delete document mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted successfully');
      setDeleteDialog({ open: false, document: null });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to delete document');
    },
  });

  const handleDeleteClick = (document: Document) => {
    setDeleteDialog({
      open: true,
      document,
    });
  };

  const handleDeleteConfirm = () => {
    if (deleteDialog.document) {
      deleteMutation.mutate(deleteDialog.document.document_id);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getStatusIcon = (status: Document['processing_status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-orange-600" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (document: Document) => {
    const { processing_status, processing_step, processing_progress } = document;
    const colors = {
      uploading: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      processing: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    };

    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          {getStatusIcon(processing_status)}
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${colors[processing_status]}`}
            title={document.error_message}
          >
            {processing_status.charAt(0).toUpperCase() + processing_status.slice(1)}
          </span>
        </div>
        {/* Show processing details and progress */}
        {(processing_status === 'processing' || processing_status === 'uploading') && (
          <div className="space-y-1">
            {processing_step && (
              <div className="text-xs text-muted-foreground">
                {processing_step.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
              </div>
            )}
            {processing_progress !== null && processing_progress !== undefined && (
              <div className="flex items-center gap-2">
                <Progress value={processing_progress} className="h-1.5 w-24" />
                <span className="text-xs text-muted-foreground font-medium">
                  {processing_progress}%
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const columns: Column<Document>[] = [
    {
      key: 'filename',
      header: 'Filename',
      sortable: true,
      render: (doc) => (
        <div className="max-w-xs">
          <div className="truncate font-medium">{doc.filename}</div>
          {doc.error_message && (
            <div className="text-xs text-red-600 truncate" title={doc.error_message}>
              {doc.error_message}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      render: (doc) => translateCategory(doc.category),
    },
    {
      key: 'upload_date',
      header: 'Upload Date',
      sortable: true,
      render: (doc) => format(new Date(doc.upload_date), 'PPp'),
    },
    {
      key: 'uploader_name',
      header: 'Uploader',
      sortable: true,
      render: (doc) => doc.uploader_name || '-',
    },
    {
      key: 'file_size_bytes',
      header: 'Size',
      sortable: true,
      render: (doc) => formatFileSize(doc.file_size_bytes),
    },
    {
      key: 'processing_status',
      header: 'Status',
      sortable: true,
      render: (doc) => getStatusBadge(doc),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (doc) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleDeleteClick(doc)}
          disabled={doc.processing_status === 'processing'}
        >
          <Trash2 className="h-4 w-4 text-red-600" />
        </Button>
      ),
    },
  ];

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Document Library</CardTitle>
          <CardDescription>
            View and manage all documents in the knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Display error if query failed */}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <h3 className="font-semibold text-destructive">Failed to load documents</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {error instanceof Error ? error.message : 'An unexpected error occurred'}
                  </p>
                </div>
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search by filename..."
              className="col-span-1 sm:col-span-2 lg:col-span-1"
            />

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={uploaderFilter} onValueChange={setUploaderFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Uploader" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Uploaders</SelectItem>
                {uploaders.map((uploader) => (
                  <SelectItem key={uploader} value={uploader!}>
                    {uploader}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={dateRangePreset} onValueChange={(value) => setDateRangePreset(value as DateRangePreset)}>
              <SelectTrigger>
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Time</SelectItem>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="last7">Last 7 Days</SelectItem>
                <SelectItem value="last30">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DataTable
            data={documentsData?.items || []}
            columns={columns}
            loading={isLoading}
            emptyTitle="No documents found"
            emptyMessage="No documents uploaded yet. Start by uploading your first document above."
            pagination={
              documentsData
                ? {
                    currentPage: documentsData.page,
                    totalPages: documentsData.total_pages,
                    onPageChange: setPage,
                    itemsPerPage: documentsData.per_page,
                    totalItems: documentsData.total,
                  }
                : undefined
            }
          />
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteDialog.open}
        onOpenChange={(open) => !open && setDeleteDialog({ open: false, document: null })}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
              <div className="space-y-3">
                <p>
                  <span className="font-semibold">Filename:</span>{' '}
                  {deleteDialog.document?.filename}
                </p>
                <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                  <p className="text-sm text-foreground">
                    <AlertCircle className="inline h-4 w-4 mr-1" />
                    <strong>Warning:</strong> This cannot be undone. The document will be
                    removed from the knowledge base and all conversations.
                  </p>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
