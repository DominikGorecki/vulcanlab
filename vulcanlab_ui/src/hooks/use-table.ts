import { useState, useMemo, useCallback } from 'react';

/**
 * Sort direction for table columns
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Return type for the useTable hook
 */
export interface UseTableReturn<TData> {
  /**
   * The sorted data array
   */
  sortedData: TData[];
  /**
   * Current sort key (property name to sort by)
   */
  sortKey: keyof TData | null;
  /**
   * Current sort direction
   */
  sortDirection: SortDirection;
  /**
   * Function to handle sorting by a column
   * @param key - The property name to sort by
   */
  handleSort: (key: keyof TData) => void;
}

/**
 * Custom hook for managing table sorting state and computing sorted data
 *
 * @param data - Array of data to be sorted
 * @param defaultSortKey - Initial sort key (column to sort by)
 * @param defaultSortDirection - Initial sort direction
 * @returns Object containing sorted data and sort control functions
 *
 * @example
 * ```tsx
 * interface User {
 *   id: number;
 *   name: string;
 *   email: string;
 * }
 *
 * function UserTable({ users }: { users: User[] }) {
 *   const { sortedData, sortKey, sortDirection, handleSort } = useTable(
 *     users,
 *     'name',
 *     'asc'
 *   );
 *
 *   return (
 *     <table>
 *       <thead>
 *         <tr>
 *           <th onClick={() => handleSort('name')}>
 *             Name {sortKey === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
 *           </th>
 *           <th onClick={() => handleSort('email')}>
 *             Email {sortKey === 'email' && (sortDirection === 'asc' ? '↑' : '↓')}
 *           </th>
 *         </tr>
 *       </thead>
 *       <tbody>
 *         {sortedData.map((user) => (
 *           <tr key={user.id}>
 *             <td>{user.name}</td>
 *             <td>{user.email}</td>
 *           </tr>
 *         ))}
 *       </tbody>
 *     </table>
 *   );
 * }
 * ```
 */
export function useTable<TData>(
  data: TData[],
  defaultSortKey: keyof TData | null = null,
  defaultSortDirection: SortDirection = 'asc'
): UseTableReturn<TData> {
  const [sortKey, setSortKey] = useState<keyof TData | null>(defaultSortKey);
  const [sortDirection, setSortDirection] =
    useState<SortDirection>(defaultSortDirection);

  const handleSort = useCallback(
    (key: keyof TData) => {
      if (sortKey === key) {
        // Toggle direction if clicking the same column
        setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
      } else {
        // New column, reset to ascending
        setSortKey(key);
        setSortDirection('asc');
      }
    },
    [sortKey]
  );

  const sortedData = useMemo(() => {
    if (!sortKey || data.length === 0) {
      return data;
    }

    return [...data].sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // Compare values
      let comparison = 0;
      if (aValue < bValue) {
        comparison = -1;
      } else if (aValue > bValue) {
        comparison = 1;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, sortKey, sortDirection]);

  return {
    sortedData,
    sortKey,
    sortDirection,
    handleSort,
  };
}
