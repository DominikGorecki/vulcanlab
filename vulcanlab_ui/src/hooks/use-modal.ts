import { useState, useCallback } from 'react';

/**
 * Options for configuring the useModal hook
 */
export interface UseModalOptions {
  /**
   * Initial open state of the modal
   * @default false
   */
  defaultOpen?: boolean;
}

/**
 * Return type for the useModal hook
 */
export interface UseModalReturn {
  /**
   * Current open state of the modal
   */
  isOpen: boolean;
  /**
   * Opens the modal
   */
  open: () => void;
  /**
   * Closes the modal
   */
  close: () => void;
  /**
   * Toggles the modal open/closed state
   */
  toggle: () => void;
}

/**
 * Custom hook for managing modal state
 *
 * @param options - Configuration options for the modal
 * @returns Object containing modal state and control functions
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const modal = useModal();
 *
 *   return (
 *     <>
 *       <button onClick={modal.open}>Open Modal</button>
 *       <Dialog open={modal.isOpen} onClose={modal.close}>
 *         <button onClick={modal.close}>Close</button>
 *       </Dialog>
 *     </>
 *   );
 * }
 * ```
 */
export function useModal(options: UseModalOptions = {}): UseModalReturn {
  const { defaultOpen = false } = options;
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const open = useCallback(() => {
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}
