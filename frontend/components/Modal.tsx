"use client";

import { X } from "lucide-react";
import { ReactNode } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: "small" | "medium" | "large" | "xlarge";
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "medium",
}: ModalProps) {
  if (!isOpen) return null;

  const sizeClasses = {
    small: "max-w-md",
    medium: "max-w-2xl",
    large: "max-w-4xl",
    xlarge: "max-w-6xl",
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="min-h-screen px-4 py-8 flex items-center justify-center">
        <div
          className={`${sizeClasses[size]} w-full bg-slate-800/95 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl shadow-black/50 animate-in zoom-in-95 duration-200 max-h-[calc(100vh-4rem)] flex flex-col my-auto`}
        >
          <div className="flex items-center justify-between p-6 border-b border-slate-700/50 bg-gradient-to-r from-slate-800 to-slate-800/50 flex-shrink-0">
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-all duration-200 hover:bg-slate-700/50 rounded-lg p-2"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="p-6 overflow-y-auto custom-scrollbar flex-1 min-h-0">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
