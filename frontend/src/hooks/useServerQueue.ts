import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queueService, type QueueItem } from '@/services/queueService';
import { toast } from 'sonner';

export function useServerQueue() {
  const queryClient = useQueryClient();

  // Fetch queue with auto-refresh every 2 seconds
  const { data: queue = [], isLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: () => queueService.getQueue(),
    refetchInterval: 2000, // Poll every 2 seconds
    refetchIntervalInBackground: true,
  });

  // Fetch queue stats
  const { data: stats } = useQuery({
    queryKey: ['queue-stats'],
    queryFn: () => queueService.getQueueStats(),
    refetchInterval: 2000,
    refetchIntervalInBackground: true,
  });

  // Remove from queue mutation
  const removeFromQueueMutation = useMutation({
    mutationFn: (queueId: string) => queueService.removeFromQueue(queueId),
    onSuccess: () => {
      toast.success('Aus Warteschlange entfernt');
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error: any) => {
      toast.error('Fehler beim Entfernen', {
        description: error.response?.data?.detail || 'Konnte nicht aus Warteschlange entfernt werden',
      });
    },
  });

  // Clear queue mutation
  const clearQueueMutation = useMutation({
    mutationFn: () => queueService.clearQueue(),
    onSuccess: (data) => {
      toast.success('Warteschlange geleert', {
        description: `${data.deleted_count} Element(e) wurden entfernt`,
      });
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error: any) => {
      toast.error('Fehler beim Leeren', {
        description: error.response?.data?.detail || 'Konnte Warteschlange nicht leeren',
      });
    },
  });

  return {
    queue,
    stats: stats || { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
    isLoading,
    removeFromQueue: removeFromQueueMutation.mutate,
    isRemoving: removeFromQueueMutation.isPending,
    clearQueue: clearQueueMutation.mutate,
    isClearing: clearQueueMutation.isPending,
  };
}
