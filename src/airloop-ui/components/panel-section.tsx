"use client";
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface PanelSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

export function PanelSection({ title, icon, children }: PanelSectionProps) {
  const [show, setShow] = useState(true);

  return (
    <div className="mb-4">
      <h2
        className="mb-3 flex cursor-pointer items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors duration-200 hover:text-slate-800"
        onClick={() => setShow(!show)}
      >
        <div className="flex items-center">
          <span className="mr-2 rounded-md bg-brand/10 p-1.5 text-brand shadow-sm">
            {icon}
          </span>
          <span>{title}</span>
        </div>
        {show ? (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronRight className="h-4 w-4 text-slate-500" />
        )}
      </h2>
      {show && children}
    </div>
  );
}
