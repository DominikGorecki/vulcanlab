import { renderHook, act } from '@testing-library/react';
import { useTable } from './use-table';

interface TestData {
  id: number;
  name: string;
  age: number;
}

describe('useTable', () => {
  const mockData: TestData[] = [
    { id: 3, name: 'Charlie', age: 25 },
    { id: 1, name: 'Alice', age: 30 },
    { id: 2, name: 'Bob', age: 20 },
  ];

  it('should return unsorted data when no sort key is provided', () => {
    const { result } = renderHook(() => useTable(mockData));

    expect(result.current.sortedData).toEqual(mockData);
    expect(result.current.sortKey).toBe(null);
    expect(result.current.sortDirection).toBe('asc');
  });

  it('should sort data in ascending order by default', () => {
    const { result } = renderHook(() => useTable(mockData, 'name'));

    expect(result.current.sortedData).toEqual([
      { id: 1, name: 'Alice', age: 30 },
      { id: 2, name: 'Bob', age: 20 },
      { id: 3, name: 'Charlie', age: 25 },
    ]);
    expect(result.current.sortKey).toBe('name');
    expect(result.current.sortDirection).toBe('asc');
  });

  it('should sort data in descending order when specified', () => {
    const { result } = renderHook(() => useTable(mockData, 'age', 'desc'));

    expect(result.current.sortedData).toEqual([
      { id: 1, name: 'Alice', age: 30 },
      { id: 3, name: 'Charlie', age: 25 },
      { id: 2, name: 'Bob', age: 20 },
    ]);
    expect(result.current.sortDirection).toBe('desc');
  });

  it('should toggle to descending when clicking the same column', () => {
    const { result } = renderHook(() => useTable(mockData, 'name', 'asc'));

    act(() => {
      result.current.handleSort('name');
    });

    expect(result.current.sortDirection).toBe('desc');
    expect(result.current.sortedData).toEqual([
      { id: 3, name: 'Charlie', age: 25 },
      { id: 2, name: 'Bob', age: 20 },
      { id: 1, name: 'Alice', age: 30 },
    ]);
  });

  it('should reset to ascending when clicking a different column', () => {
    const { result } = renderHook(() => useTable(mockData, 'name', 'desc'));

    act(() => {
      result.current.handleSort('age');
    });

    expect(result.current.sortKey).toBe('age');
    expect(result.current.sortDirection).toBe('asc');
    expect(result.current.sortedData).toEqual([
      { id: 2, name: 'Bob', age: 20 },
      { id: 3, name: 'Charlie', age: 25 },
      { id: 1, name: 'Alice', age: 30 },
    ]);
  });

  it('should handle empty data array', () => {
    const { result } = renderHook(() => useTable<TestData>([], 'name'));

    expect(result.current.sortedData).toEqual([]);
  });

  it('should handle data with null/undefined values', () => {
    const dataWithNulls = [
      { id: 1, name: 'Alice', age: 30 },
      { id: 2, name: null as unknown as string, age: 20 },
      { id: 3, name: 'Charlie', age: 25 },
    ];

    const { result } = renderHook(() => useTable(dataWithNulls, 'name'));

    // Null values should be sorted to the end
    expect(result.current.sortedData[0].name).toBe('Alice');
    expect(result.current.sortedData[1].name).toBe('Charlie');
    expect(result.current.sortedData[2].name).toBe(null);
  });

  it('should maintain original array reference when data changes', () => {
    const { result, rerender } = renderHook(
      ({ data }) => useTable(data, 'name'),
      {
        initialProps: { data: mockData },
      }
    );

    const firstSortedData = result.current.sortedData;

    const newData = [
      { id: 4, name: 'David', age: 35 },
      ...mockData,
    ];

    rerender({ data: newData });

    expect(result.current.sortedData).not.toBe(firstSortedData);
    expect(result.current.sortedData.length).toBe(4);
  });

  it('should preserve original data immutability', () => {
    const { result } = renderHook(() => useTable(mockData, 'name'));

    expect(result.current.sortedData).not.toBe(mockData);
    expect(mockData[0].name).toBe('Charlie'); // Original order unchanged
  });

  it('should handle numeric sorting correctly', () => {
    const { result } = renderHook(() => useTable(mockData, 'id'));

    expect(result.current.sortedData).toEqual([
      { id: 1, name: 'Alice', age: 30 },
      { id: 2, name: 'Bob', age: 20 },
      { id: 3, name: 'Charlie', age: 25 },
    ]);
  });

  it('should toggle between asc and desc multiple times', () => {
    const { result } = renderHook(() => useTable(mockData, 'name', 'asc'));

    // First click: desc
    act(() => {
      result.current.handleSort('name');
    });
    expect(result.current.sortDirection).toBe('desc');

    // Second click: asc
    act(() => {
      result.current.handleSort('name');
    });
    expect(result.current.sortDirection).toBe('asc');

    // Third click: desc
    act(() => {
      result.current.handleSort('name');
    });
    expect(result.current.sortDirection).toBe('desc');
  });
});
