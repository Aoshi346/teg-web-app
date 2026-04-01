"use client";

import React, { useState, useRef, useEffect } from "react";
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
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selected = options.find((o) => o.id === value);

  const filtered = query.trim()
    ? options.filter((o) =>
        o.label.toLowerCase().includes(query.toLowerCase()),
      )
    : options;

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

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

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => {
          if (!disabled) {
            setOpen(!open);
            if (!open) setTimeout(() => inputRef.current?.focus(), 50);
          }
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
        <span className={`flex-1 truncate ${selected ? "text-gray-900" : "text-gray-400"}`}>
          {selected ? selected.label : placeholder}
        </span>
        {allowClear && selected && !disabled ? (
          <X className="w-4 h-4 text-gray-400 hover:text-gray-600 flex-shrink-0" onClick={handleClear} />
        ) : (
          <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
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
                    {isSelected && <Check className="w-4 h-4 text-indigo-500 flex-shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
