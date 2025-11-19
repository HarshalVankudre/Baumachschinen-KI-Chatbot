import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { documentService } from '@/services/documentService';
import type { Document } from '@/types';

/**
 * Hook to subscribe to real-time document processing updates via SSE
 *
 * Automatically subscribes to processing updates for documents that are
 * currently uploading or processing, and updates the query cache when
 * status changes are received.
 *
 * @param documents - List of documents to monitor
 */
export function useDocumentUpdates(documents: Document[] | undefined) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!documents || documents.length === 0) {
      return;
    }

    // Find documents that are currently being processed
    const processingDocs = documents.filter(
      (doc) => doc.processing_status === 'uploading' || doc.processing_status === 'processing'
    );

    if (processingDocs.length === 0) {
      return;
    }

    console.log(`[SSE] Subscribing to ${processingDocs.length} processing documents`);

    // Subscribe to updates for each processing document
    const unsubscribeFunctions = processingDocs.map((doc) => {
      return documentService.subscribeToDocumentUpdates(
        doc.document_id,
        (data) => {
          console.log(`[SSE] Update received for ${doc.document_id}:`, data);

          // Ignore connection messages
          if (data.type === 'connected') {
            return;
          }

          // Handle current state message
          if (data.type === 'state') {
            console.log(`[SSE] Received current state for ${doc.document_id}:`, data.processing_status);
            // Continue processing as normal update
          }

          // Update the query cache with new document status
          queryClient.setQueryData<any>(['documents'], (oldData: any) => {
            if (!oldData || !oldData.items) return oldData;

            return {
              ...oldData,
              items: oldData.items.map((item: Document) =>
                item.document_id === doc.document_id
                  ? {
                      ...item,
                      processing_status: data.processing_status || item.processing_status,
                      processing_step: data.processing_step,
                      processing_progress: data.processing_progress,
                      error_message: data.error_message,
                      chunk_count: data.chunk_count || item.chunk_count,
                    }
                  : item
              ),
            };
          });

          // If processing is complete or failed, refetch to get final state
          if (data.processing_status === 'completed' || data.processing_status === 'failed') {
            console.log(`[SSE] Document ${doc.document_id} finished with status: ${data.processing_status}`);

            // Refetch after a short delay to ensure backend has committed all changes
            setTimeout(() => {
              queryClient.invalidateQueries({ queryKey: ['documents'] });
            }, 500);
          }
        }
      );
    });

    // Cleanup: close all SSE connections when component unmounts or dependencies change
    return () => {
      console.log(`[SSE] Cleaning up ${unsubscribeFunctions.length} subscriptions`);
      unsubscribeFunctions.forEach((unsubscribe) => unsubscribe());
    };
  }, [documents, queryClient]);
}
