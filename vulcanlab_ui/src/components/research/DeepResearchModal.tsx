"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Beaker, UserCog } from "lucide-react";
import { ManualResearchWizard } from "./ManualResearchWizard";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DeepResearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  collectionId: number;
  initialSessionId?: number;
}

export function DeepResearchModal({
  isOpen,
  onClose,
  collectionId,
  initialSessionId,
}: DeepResearchModalProps) {
  const [selectedMode, setSelectedMode] = useState<'manual' | 'automated' | null>(
    initialSessionId ? 'manual' : null
  );

  const [sessionId, setSessionId] = useState<number | null>(initialSessionId || null);
  const { toast } = useToast();

  // Update state when initialSessionId changes or modal opens
  useEffect(() => {
    if (isOpen && initialSessionId) {
      setSelectedMode('manual');
      setSessionId(initialSessionId);
    } else if (isOpen && !initialSessionId) {
      setSelectedMode(null);
      setSessionId(null);
    }
  }, [isOpen, initialSessionId]);

  const handleModeSelect = async (mode: 'manual' | 'automated') => {
    setSelectedMode(mode);
    
    if (mode === 'manual') {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            collection_id: collectionId,
            session_type: 'manual',
          }),
        });
        
        if (!response.ok) {
          throw new Error('Failed to create research session');
        }
        
        const data = await response.json();
        setSessionId(data.id);
      } catch (error) {
        console.error('Error creating research session:', error);
      }
    } else {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/start-automated`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            collection_id: collectionId,
          }),
        });
        
        if (!response.ok) {
          throw new Error('Failed to start automated research');
        }
        
        toast({
          title: "Automated research started",
          description: "The system is researching in the background.",
        });
        
        onClose();
      } catch (error) {
        console.error('Error starting automated research:', error);
        toast({
          title: "Failed to start research",
          description: error instanceof Error ? error.message : "Unknown error",
          variant: "destructive",
        });
      }
    }
  };

  if (selectedMode === 'manual' && sessionId) {
    return (
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="sm:max-w-[900px] h-[85vh] flex flex-col p-0">
          <DialogHeader className="sr-only">
            <DialogTitle>Manual Research Wizard</DialogTitle>
            <DialogDescription>
              Conduct manual research step by step
            </DialogDescription>
          </DialogHeader>
          <ManualResearchWizard 
            collectionId={collectionId} 
            sessionId={sessionId} 
            onComplete={onClose} 
          />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Start Deep Research</DialogTitle>
          <DialogDescription>
            Choose how you want to conduct research on this collection
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Card 
            className="cursor-pointer hover:border-primary transition-colors flex flex-col"
            onClick={() => handleModeSelect('manual')}
          >
            <CardHeader>
              <div className="mb-2 p-2 w-fit rounded-lg bg-primary/10 text-primary">
                <UserCog className="h-6 w-6" />
              </div>
              <CardTitle>Manual Research</CardTitle>
              <CardDescription>
                Step-by-step guided workflow. You control LLM interactions and paste responses.
              </CardDescription>
            </CardHeader>
            <CardContent className="mt-auto flex justify-end">
              <Button onClick={(e) => {
                e.stopPropagation();
                handleModeSelect('manual');
              }}>
                Start Manual
              </Button>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer hover:border-primary transition-colors flex flex-col"
            onClick={() => handleModeSelect('automated')}
          >
            <CardHeader>
              <div className="mb-2 p-2 w-fit rounded-lg bg-primary/10 text-primary">
                <Beaker className="h-6 w-6" />
              </div>
              <CardTitle>Automated Research</CardTitle>
              <CardDescription>
                Fully automated using LangGraph. System handles all LLM calls.
              </CardDescription>
            </CardHeader>
            <CardContent className="mt-auto flex justify-end">
              <Button onClick={(e) => {
                e.stopPropagation();
                handleModeSelect('automated');
              }}>
                Start Automated
              </Button>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
