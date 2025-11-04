import { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from './EmptyState';
import { ChevronUp, ChevronDown, ChevronsUpDown, Database } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: {
    label: string;
    onClick: () => void;
  };
  pagination?: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    itemsPerPage?: number;
    totalItems?: number;
  };
  onRowClick?: (item: T) => void;
  rowClassName?: (item: T) => string;
}

type SortDirection = 'asc' | 'desc' | null;

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  emptyTitle = 'Keine Daten verfügbar',
  emptyMessage = 'Es gibt derzeit keine anzuzeigenden Elemente.',
  emptyAction,
  pagination,
  onRowClick,
  rowClassName,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (columnKey: string) => {
    if (sortKey === columnKey) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortDirection(null);
        setSortKey(null);
      }
    } else {
      setSortKey(columnKey);
      setSortDirection('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      // For dates
      const aTime = new Date(aValue).getTime();
      const bTime = new Date(bValue).getTime();
      if (!isNaN(aTime) && !isNaN(bTime)) {
        return sortDirection === 'asc' ? aTime - bTime : bTime - aTime;
      }

      return 0;
    });
  }, [data, sortKey, sortDirection]);

  const renderSortIcon = (columnKey: string) => {
    if (sortKey !== columnKey) {
      return <ChevronsUpDown className="h-4 w-4 ml-2" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="h-4 w-4 ml-2" />
    ) : (
      <ChevronDown className="h-4 w-4 ml-2" />
    );
  };

  if (loading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.key} className={column.className}>
                  {column.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                {columns.map((column) => (
                  <TableCell key={column.key}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-md border p-8">
        <EmptyState
          icon={Database}
          title={emptyTitle}
          message={emptyMessage}
          actionLabel={emptyAction?.label}
          onAction={emptyAction?.onClick}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.key} className={column.className}>
                  {column.sortable ? (
                    <button
                      onClick={() => handleSort(column.key)}
                      className="flex items-center font-medium hover:text-foreground transition-colors"
                      aria-label={`Sort by ${column.header}`}
                    >
                      {column.header}
                      {renderSortIcon(column.key)}
                    </button>
                  ) : (
                    column.header
                  )}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedData.map((item, index) => (
              <TableRow
                key={index}
                onClick={() => onRowClick?.(item)}
                className={cn(
                  onRowClick && 'cursor-pointer hover:bg-muted/50',
                  rowClassName?.(item)
                )}
              >
                {columns.map((column) => (
                  <TableCell key={column.key} className={column.className}>
                    {column.render ? column.render(item) : item[column.key]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {pagination && pagination.totalPages > 1 && (
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            {pagination.totalItems && pagination.itemsPerPage && (
              <>
                Zeige{' '}
                {Math.min(
                  (pagination.currentPage - 1) * pagination.itemsPerPage + 1,
                  pagination.totalItems
                )}{' '}
                bis{' '}
                {Math.min(
                  pagination.currentPage * pagination.itemsPerPage,
                  pagination.totalItems
                )}{' '}
                von {pagination.totalItems} Ergebnissen
              </>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.currentPage - 1)}
              disabled={pagination.currentPage === 1}
            >
              Zurück
            </Button>
            <div className="text-sm">
              Seite {pagination.currentPage} von {pagination.totalPages}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.currentPage + 1)}
              disabled={pagination.currentPage === pagination.totalPages}
            >
              Weiter
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
