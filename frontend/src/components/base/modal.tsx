"use client";

import { ReactNode, ElementType, useEffect, useRef } from "react";
import { X, ArrowDownLeft } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  icon?: ElementType;
  children: ReactNode;
}

const FOCUSABLE =
  'a[href], area[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function Modal({ isOpen, onClose, title, icon: Icon, children }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  // Escape to close, body scroll lock, focus trap, restore focus on close.
  useEffect(() => {
    if (!isOpen) return;

    previouslyFocused.current = document.activeElement as HTMLElement | null;

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Focus the first focusable element (or the dialog itself).
    queueMicrotask(() => {
      const dialog = dialogRef.current;
      if (!dialog) return;
      const first = dialog.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? dialog).focus();
    });

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;

      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusables = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (focusables.length === 0) {
        e.preventDefault();
        dialog.focus();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;

      if (e.shiftKey && (active === first || !dialog.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", onKey);

    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      previouslyFocused.current?.focus?.();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="
        flex z-1500
        fixed inset-0 
        items-center 
        justify-center 
        bg-generate-background/20 
        backdrop-blur-sm
        animate-in fade-in duration-200"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="generate-modal-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        
        className="flex flex-col w-[25%]"
      >

        {/* Modal Header */}
        <div className="generate-section-header items-center justify-between">
          {Icon && <Icon className="icon"/>}
          <span id="generate-modal-title" className="font-bold">{title}</span>
          <button
            onClick={onClose}
            aria-label="Close"
            className="hover:text-generate-selected"
          >
            <ArrowDownLeft className="icon" />
          </button>
        </div>
 
        {/* Modal Body */}
        <div className="generate-section-analysis">{children}</div>
      </div>
    </div>
  );
}
