import { renderHook, act } from '@testing-library/react';
import { useAddToCollection } from '../use-add-to-collection';

describe('useAddToCollection', () => {
  it('should initialize with closed state and empty item info', () => {
    const { result } = renderHook(() => useAddToCollection());
    expect(result.current.isOpen).toBe(false);
    expect(result.current.itemType).toBe("");
    expect(result.current.itemLink).toBe("");
  });

  it('should update state when openAddToCollection is called', () => {
    const { result } = renderHook(() => useAddToCollection());
    
    act(() => {
      result.current.openAddToCollection("excerpt", "/some/link");
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.itemType).toBe("excerpt");
    expect(result.current.itemLink).toBe("/some/link");
  });

  it('should set isOpen to false when closeAddToCollection is called', () => {
    const { result } = renderHook(() => useAddToCollection());
    
    act(() => {
      result.current.openAddToCollection("excerpt", "/some/link");
    });
    expect(result.current.isOpen).toBe(true);

    act(() => {
      result.current.closeAddToCollection();
    });
    expect(result.current.isOpen).toBe(false);
    // Note: itemType and itemLink might still persist depending on implementation, 
    // but the key behavior is isOpen being false.
  });
});

