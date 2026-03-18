"use client";

import { ReactNode, ElementType } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  icon?: ElementType; // Type for Lucide icons
  children: ReactNode;
}

export default function Modal({ isOpen, onClose, title, icon: Icon, children }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-dsi-analysis border border-dsi-outline/20 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-dsi-outline/10 bg-dsi-background/30">
          <h3 className="text-lg font-bold flex items-center gap-2">
            {Icon && <Icon className="w-5 h-5 text-dsi-selected" />}
            {title}
          </h3>
          <button 
            onClick={onClose} 
            className="p-1 hover:bg-dsi-outline/10 rounded text-dsi-selected transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto">
          {children}
        </div>

      </div>
    </div>
  );
}