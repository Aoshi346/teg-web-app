"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { Search, ChevronDown, X, Check } from "lucide-react";

interface ComboboxOption {
  id: number;
  label: string;
}

interface ComboboxProps {
  options: ComboboxOption[];
  value: number | "" | null | undefined;
  onChange: (value: number | "") => void;
  placeholder?: string;
  emptyLabel?: string;
  error?: boolean;
  disabled?: boolean;
  allowClear?: boolean;
  icon?: React.ReactNode;
}

export default function Combobox({
  options,
  value,
  onChange,
  placeholder = "Buscar...",
  emptyLabel = "Sin opciones disponibles",
  error,
  disabled,
  allowClear,
  icon,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [mounted, setMounted] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number; width: number }>({
    top: 0,
    left: 0,
    width: 0,
  });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selected = options.find((o) => o.id === value);

  const filtered = query.trim()
    ? options.filter((o) =>
        o.label.toLowerCase().includes(query.toLowerCase()),
      )
    : options;

  useEffect(() => setMounted(true), []);

  // Compute position when opening
  const updatePos = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPos({
      top: rect.bottom + window.scrollY + 4,
      left: rect.left + window.scrollX,
      width: rect.width,
    });
  }, []);

  useEffect(() => {
    if (open) {
      updatePos();
      setTimeout(() => inputRef.current?.focus(), 30);
    } else {
      setQuery("");
    }
  }, [open, updatePos]);

  // Reposition on scroll/resize while open
  useEffect(() => {
    if (!open) return;
    const handler = () => updatePos();
    window.addEventListener("scroll", handler, true);
    window.addEventListener("resize", handler);
    return () => {
      window.removeEventListener("scroll", handler, true);
      window.removeEventListener("resize", handler);
    };
  }, [open, updatePos]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      const target = e.target as Node;
      if (
        triggerRef.current?.contains(target) ||
        dropdownRef.current?.contains(target)
      )
        return;
      setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  const handleSelect = (id: number) => {
    onChange(id);
    setOpen(false);
    setQuery("");
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange("");
    setQuery("");
  };

  const dropdown = (
    <div
      ref={dropdownRef}
      style={{ position: "absolute", top: pos.top, left: pos.left, width: pos.width }}
      className="z-[9999] bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150"
    >
      {/* Search */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-100">
        <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="flex-1 text-sm outline-none bg-transparent placeholder:text-gray-400"
        />
        {query && (
          <button type="button" onClick={() => setQuery("")}>
            <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Options */}
      <div className="max-h-48 overflow-y-auto overscroll-contain">
        {filtered.length === 0 ? (
          <div className="px-3 py-4 text-center text-sm text-gray-400">
            {emptyLabel}
          </div>
        ) : (
          filtered.map((opt) => {
            const isSelected = opt.id === value;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleSelect(opt.id)}
                className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
                  isSelected
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-gray-700 hover:bg-gray-50"
                }`}
              >
                <span className="flex-1 truncate">{opt.label}</span>
                {isSelected && (
                  <Check className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );

  return (
    <div className="relative">
      {/* Trigger */}
      <button
        ref={triggerRef}
        type="button"
        disabled={disabled}
        onClick={() => {
          if (!disabled) setOpen(!open);
        }}
        className={`w-full flex items-center gap-2 px-3 py-2.5 bg-white border rounded-lg shadow-sm text-sm font-medium text-left transition-all ${
          error
            ? "border-red-300 focus:border-red-500 ring-2 ring-red-100"
            : open
              ? "border-indigo-400 ring-2 ring-indigo-100"
              : "border-gray-200 hover:border-gray-300"
        } ${disabled ? "opacity-60 cursor-not-allowed bg-gray-50" : "cursor-pointer"}`}
      >
        {icon && <span className="flex-shrink-0 text-gray-400">{icon}</span>}
        <span
          className={`flex-1 truncate ${selected ? "text-gray-900" : "text-gray-400"}`}
        >
          {selected ? selected.label : placeholder}
        </span>
        {allowClear && selected && !disabled ? (
          <X
            className="w-4 h-4 text-gray-400 hover:text-gray-600 flex-shrink-0"
            onClick={handleClear}
          />
        ) : (
          <ChevronDown
            className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
          />
        )}
      </button>

      {/* Portal dropdown */}
      {mounted && open && createPortal(dropdown, document.body)}
    </div>
  );
}
