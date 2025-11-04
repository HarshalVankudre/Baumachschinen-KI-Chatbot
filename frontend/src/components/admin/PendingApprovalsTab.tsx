import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Check, X } from 'lucide-react';
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { DataTable, type Column } from '@/components/shared/DataTable';
import { EmptyState } from '@/components/shared/EmptyState';
import { adminService } from '@/services/adminService';
import { toast } from 'sonner';
import type { PendingUser } from '@/types';

interface ApprovalDialogState {
  open: boolean;
  userId: string | null;
  username: string | null;
  level: 'regular' | 'superuser' | 'admin' | null;
}

interface RejectDialogState {
  open: boolean;
  userId: string | null;
  username: string | null;
  reason: string;
}

export function PendingApprovalsTab() {
  const _queryClient = useQueryClient();

  const [approvalDialog, setApprovalDialog] = useState<ApprovalDialogState>({
    open: false,
    userId: null,
    username: null,
    level: null,
  });

  const [rejectDialog, setRejectDialog] = useState<RejectDialogState>({
    open: false,
    userId: null,
    username: null,
    reason: '',
  });

  // Fetch pending users
  const { data: pendingUsers = [], isLoading, refetch } = useQuery({
    queryKey: ['pendingUsers'],
    queryFn: () => adminService.getPendingUsers(),
  });

  // Approve user mutation
  const approveMutation = useMutation({
    mutationFn: ({
      userId,
      level,
    }: {
      userId: string;
      level: 'regular' | 'superuser' | 'admin';
    }) => adminService.approveUser(userId, level),
    onSuccess: () => {
      refetch();
      toast.success('Benutzer erfolgreich genehmigt');
      setApprovalDialog({ open: false, userId: null, username: null, level: null });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Genehmigung fehlgeschlagen');
    },
  });

  // Reject user mutation
  const rejectMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason?: string }) =>
      adminService.rejectUser(userId, reason),
    onSuccess: () => {
      refetch();
      toast.success('Benutzer erfolgreich abgelehnt');
      setRejectDialog({ open: false, userId: null, username: null, reason: '' });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Ablehnung fehlgeschlagen');
    },
  });

  const handleApproveClick = (
    userId: string,
    username: string,
    level: 'regular' | 'superuser' | 'admin'
  ) => {
    setApprovalDialog({
      open: true,
      userId,
      username,
      level,
    });
  };

  const handleRejectClick = (userId: string, username: string) => {
    setRejectDialog({
      open: true,
      userId,
      username,
      reason: '',
    });
  };

  const handleApproveConfirm = () => {
    if (approvalDialog.userId && approvalDialog.level) {
      approveMutation.mutate({
        userId: approvalDialog.userId,
        level: approvalDialog.level,
      });
    }
  };

  const handleRejectConfirm = () => {
    if (rejectDialog.userId) {
      rejectMutation.mutate({
        userId: rejectDialog.userId,
        reason: rejectDialog.reason || undefined,
      });
    }
  };

  const columns: Column<PendingUser>[] = [
    {
      key: 'username',
      header: 'Benutzername',
      sortable: true,
    },
    {
      key: 'email',
      header: 'E-Mail',
      sortable: true,
    },
    {
      key: 'created_at',
      header: 'Registrierungsdatum',
      sortable: true,
      render: (user) => format(new Date(user.created_at), 'PPp'),
    },
    {
      key: 'email_verified',
      header: 'E-Mail verifiziert',
      render: (user) => (
        <div className="flex items-center">
          {user.email_verified ? (
            <Check className="w-5 h-5 text-green-600" />
          ) : (
            <X className="w-5 h-5 text-red-600" />
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Aktionen',
      render: (user) => (
        <div className="flex gap-2 items-center">
          <Select
            onValueChange={(value) =>
              handleApproveClick(
                user.user_id,
                user.username,
                value as 'regular' | 'superuser' | 'admin'
              )
            }
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Genehmigen als..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="regular">Normaler Benutzer</SelectItem>
              <SelectItem value="superuser">Superuser</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => handleRejectClick(user.user_id, user.username)}
          >
            Ablehnen
          </Button>
        </div>
      ),
    },
  ];

  if (!isLoading && pendingUsers.length === 0) {
    return (
      <EmptyState
        icon={Check}
        title="Keine ausstehenden Genehmigungen"
        message="Alle Benutzer wurden bearbeitet."
      />
    );
  }

  return (
    <>
      <DataTable
        data={pendingUsers}
        columns={columns}
        loading={isLoading}
        emptyTitle="Keine ausstehenden Genehmigungen"
        emptyMessage="Alle Benutzer wurden bearbeitet."
      />

      {/* Approval Confirmation Dialog */}
      <AlertDialog
        open={approvalDialog.open}
        onOpenChange={(open) =>
          !open &&
          setApprovalDialog({ open: false, userId: null, username: null, level: null })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Benutzer genehmigen</AlertDialogTitle>
            <AlertDialogDescription>
              Benutzer "{approvalDialog.username}" genehmigen als{' '}
              {approvalDialog.level === 'regular'
                ? 'Normaler Benutzer'
                : approvalDialog.level === 'superuser'
                ? 'Superuser'
                : 'Admin'}
              ?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleApproveConfirm}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? 'Wird genehmigt...' : 'Genehmigen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reject Confirmation Dialog */}
      <AlertDialog
        open={rejectDialog.open}
        onOpenChange={(open) =>
          !open && setRejectDialog({ open: false, userId: null, username: null, reason: '' })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Benutzer ablehnen</AlertDialogTitle>
            <AlertDialogDescription>
              Benutzer "{rejectDialog.username}" ablehnen?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Label htmlFor="reason" className="text-sm font-medium">
              Grund (optional)
            </Label>
            <Textarea
              id="reason"
              placeholder="Grund für Ablehnung eingeben..."
              value={rejectDialog.reason}
              onChange={(e) =>
                setRejectDialog((prev) => ({ ...prev, reason: e.target.value }))
              }
              className="mt-2"
              rows={3}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRejectConfirm}
              disabled={rejectMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {rejectMutation.isPending ? 'Wird abgelehnt...' : 'Ablehnen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
