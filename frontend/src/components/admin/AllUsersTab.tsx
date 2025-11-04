import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
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
import { DataTable, type Column } from '@/components/shared/DataTable';
import { SearchInput } from '@/components/shared/SearchInput';
import { useDebounce } from '@/hooks/useDebounce';
import { adminService } from '@/services/adminService';
import { toast } from 'sonner';
import type { User } from '@/types';
import { translateStatus, getStatusOptions } from '@/utils/translations';

interface ChangeAuthDialogState {
  open: boolean;
  user: User | null;
  newLevel: 'regular' | 'superuser' | 'admin' | null;
}

interface SuspendDialogState {
  open: boolean;
  user: User | null;
  action: 'suspend' | 'activate' | null;
}

export function AllUsersTab() {
  const _queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(search, 300);

  const [changeAuthDialog, setChangeAuthDialog] = useState<ChangeAuthDialogState>({
    open: false,
    user: null,
    newLevel: null,
  });

  const [suspendDialog, setSuspendDialog] = useState<SuspendDialogState>({
    open: false,
    user: null,
    action: null,
  });

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, statusFilter, levelFilter]);

  // Fetch users
  const { data: usersData, isLoading, refetch } = useQuery({
    queryKey: ['users', debouncedSearch, statusFilter, levelFilter, page],
    queryFn: () =>
      adminService.getUsers({
        search: debouncedSearch || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        authorization_level: levelFilter !== 'all' ? levelFilter : undefined,
        page,
      }),
  });

  // Change authorization mutation
  const changeAuthMutation = useMutation({
    mutationFn: ({
      userId,
      level,
    }: {
      userId: string;
      level: 'regular' | 'superuser' | 'admin';
    }) => adminService.updateUserAuthorization(userId, level),
    onSuccess: () => {
      refetch();
      toast.success('Autorisierungsstufe geändert');
      setChangeAuthDialog({ open: false, user: null, newLevel: null });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Fehler beim Ändern der Autorisierungsstufe');
    },
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({
      userId,
      status,
    }: {
      userId: string;
      status: 'active' | 'suspended';
    }) => adminService.updateUserStatus(userId, status),
    onSuccess: (_, variables) => {
      refetch();
      toast.success(
        variables.status === 'suspended'
          ? 'Benutzer erfolgreich gesperrt'
          : 'Benutzer erfolgreich aktiviert'
      );
      setSuspendDialog({ open: false, user: null, action: null });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Fehler beim Aktualisieren des Benutzerstatus');
    },
  });

  const handleChangeAuthClick = (user: User, newLevel: 'regular' | 'superuser' | 'admin') => {
    if (newLevel !== user.authorization_level) {
      setChangeAuthDialog({
        open: true,
        user,
        newLevel,
      });
    }
  };

  const handleChangeAuthConfirm = () => {
    if (changeAuthDialog.user && changeAuthDialog.newLevel) {
      changeAuthMutation.mutate({
        userId: changeAuthDialog.user.user_id,
        level: changeAuthDialog.newLevel,
      });
    }
  };

  const handleSuspendClick = (user: User, action: 'suspend' | 'activate') => {
    setSuspendDialog({
      open: true,
      user,
      action,
    });
  };

  const handleSuspendConfirm = () => {
    if (suspendDialog.user && suspendDialog.action) {
      updateStatusMutation.mutate({
        userId: suspendDialog.user.user_id,
        status: suspendDialog.action === 'suspend' ? 'suspended' : 'active',
      });
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case 'regular':
        return 'Normaler Benutzer';
      case 'superuser':
        return 'Superuser';
      case 'admin':
        return 'Admin';
      default:
        return level;
    }
  };

  const columns: Column<User>[] = [
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
      key: 'authorization_level',
      header: 'Autorisierungsstufe',
      sortable: true,
      render: (user) => {
        const colors = {
          regular: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
          superuser: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
          admin: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
        };
        return (
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              colors[user.authorization_level]
            }`}
          >
            {getLevelLabel(user.authorization_level)}
          </span>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (user) => {
        const status = user.status || 'active';
        const colors = {
          active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
          suspended: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
          rejected: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status]}`}>
            {translateStatus(status)}
          </span>
        );
      },
    },
    {
      key: 'last_login',
      header: 'Letzte Anmeldung',
      sortable: true,
      render: (user) =>
        user.last_login ? format(new Date(user.last_login), 'PPp') : 'Nie',
    },
    {
      key: 'actions',
      header: 'Aktionen',
      render: (user) => (
        <div className="flex gap-2 items-center flex-wrap">
          <Select
            value={user.authorization_level}
            onValueChange={(value) =>
              handleChangeAuthClick(user, value as 'regular' | 'superuser' | 'admin')
            }
          >
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="regular">Normaler Benutzer</SelectItem>
              <SelectItem value="superuser">Superuser</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
          {user.status !== 'suspended' ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSuspendClick(user, 'suspend')}
            >
              Sperren
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSuspendClick(user, 'activate')}
            >
              Aktivieren
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <div className="space-y-4">
        <div className="flex gap-4 flex-wrap">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Nach Benutzername oder E-Mail suchen..."
            className="flex-1 min-w-[200px]"
          />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Alle Status</SelectItem>
              {getStatusOptions().map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Autorisierungsstufe" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Alle Stufen</SelectItem>
              <SelectItem value="regular">Normaler Benutzer</SelectItem>
              <SelectItem value="superuser">Superuser</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <DataTable
          data={usersData?.items || []}
          columns={columns}
          loading={isLoading}
          emptyTitle="Keine Benutzer gefunden"
          emptyMessage="Keine Benutzer entsprechen Ihren Suchkriterien."
          pagination={
            usersData
              ? {
                  currentPage: usersData.page,
                  totalPages: usersData.total_pages,
                  onPageChange: setPage,
                  itemsPerPage: usersData.per_page,
                  totalItems: usersData.total,
                }
              : undefined
          }
        />
      </div>

      {/* Change Authorization Confirmation Dialog */}
      <AlertDialog
        open={changeAuthDialog.open}
        onOpenChange={(open) =>
          !open && setChangeAuthDialog({ open: false, user: null, newLevel: null })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Autorisierungsstufe ändern</AlertDialogTitle>
            <AlertDialogDescription>
              Autorisierungsstufe für "{changeAuthDialog.user?.username}" ändern?
              <div className="mt-4 space-y-2">
                <div>
                  <span className="font-semibold">Aktuell:</span>{' '}
                  {getLevelLabel(changeAuthDialog.user?.authorization_level || '')}
                </div>
                <div>
                  <span className="font-semibold">Neu:</span>{' '}
                  {getLevelLabel(changeAuthDialog.newLevel || '')}
                </div>
              </div>
              <p className="mt-4 text-sm">
                Hinweis: Die Änderung wird bei der nächsten Anmeldung wirksam.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleChangeAuthConfirm}
              disabled={changeAuthMutation.isPending}
            >
              {changeAuthMutation.isPending ? 'Wird geändert...' : 'Ändern'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Suspend/Activate Confirmation Dialog */}
      <AlertDialog
        open={suspendDialog.open}
        onOpenChange={(open) =>
          !open && setSuspendDialog({ open: false, user: null, action: null })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {suspendDialog.action === 'suspend' ? 'Benutzer sperren' : 'Benutzer aktivieren'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {suspendDialog.action === 'suspend' ? (
                <>
                  Benutzer "{suspendDialog.user?.username}" sperren?
                  <p className="mt-2">Sie werden sofort abgemeldet.</p>
                </>
              ) : (
                <>
                  Benutzer "{suspendDialog.user?.username}" aktivieren?
                  <p className="mt-2">Sie können sich wieder anmelden.</p>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleSuspendConfirm}
              disabled={updateStatusMutation.isPending}
              className={
                suspendDialog.action === 'suspend'
                  ? 'bg-destructive hover:bg-destructive/90'
                  : ''
              }
            >
              {updateStatusMutation.isPending
                ? suspendDialog.action === 'suspend'
                  ? 'Wird gesperrt...'
                  : 'Wird aktiviert...'
                : suspendDialog.action === 'suspend'
                ? 'Sperren'
                : 'Aktivieren'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
