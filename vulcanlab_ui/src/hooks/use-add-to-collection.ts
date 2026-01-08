"use client";

import { useState, useCallback } from "react";

interface UseAddToCollectionReturn {
  isOpen: boolean;
  itemType: string;
  itemLink: string;
  openAddToCollection: (type: string, link: string) => void;
  closeAddToCollection: () => void;
}

/**
 * Hook to manage the state of the AddToCollectionModal.
 */
export function useAddToCollection(): UseAddToCollectionReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [itemType, setItemType] = useState("");
  const [itemLink, setItemLink] = useState("");

  const openAddToCollection = useCallback((type: string, link: string) => {
    setItemType(type);
    setItemLink(link);
    setIsOpen(true);
  }, []);

  const closeAddToCollection = useCallback(() => {
    setIsOpen(false);
  }, []);

  return {
    isOpen,
    itemType,
    itemLink,
    openAddToCollection,
    closeAddToCollection,
  };
}

