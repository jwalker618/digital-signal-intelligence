"use client";

import { ReactNode, ElementType, useEffect } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  icon?: ElementType;
  children: ReactNode;
}

export default function Modal({ isOpen, onClose, title, icon: Icon, children }: ModalProps) {
  // Close on Escape + lock body scroll while open.
  useEffect(() => {
    if (!isOpen) return;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dsi-modal-title"
      onClick={onClose}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-dsi-analysis border border-dsi-outline/20 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-dsi-outline/10 bg-dsi-background/30">
          <h3 id="dsi-modal-title" className="text-lg font-bold flex items-center gap-2">
            {Icon && <Icon className="w-5 h-5 text-dsi-selected" />}
            {title}
          </h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="p-1 hover:bg-dsi-outline/10 rounded text-dsi-selected transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
