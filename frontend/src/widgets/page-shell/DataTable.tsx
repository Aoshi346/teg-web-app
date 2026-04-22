import React from "react";
import { cn } from "@shared/lib/utils";
import { Surface } from "@shared/ui/Surface";

export interface ColumnDef<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  width?: string;
  align?: "left" | "right" | "center";
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  rowAccent?: (row: T) => "teg" | "pteg" | null;
  empty?: React.ReactNode;
  className?: string;
  getRowKey?: (row: T) => string | number;
}

const ALIGN_TH: Record<string, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

const ALIGN_TD: Record<string, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

const ACCENT_ROW: Record<string, string> = {
  teg: "hover:bg-[color:var(--color-accent-teg-soft)] hover:shadow-[inset_2px_0_0_var(--color-accent-teg)]",
  pteg: "hover:bg-[color:var(--color-accent-pteg-soft)] hover:shadow-[inset_2px_0_0_var(--color-accent-pteg)]",
};

export function DataTable<T>({
  columns,
  data,
  onRowClick,
  rowAccent,
  empty,
  className,
  getRowKey,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <Surface className={cn("overflow-hidden p-0", className)}>
        <div className="h-32 flex items-center justify-center font-mono text-xs text-slate-400">
          {empty ?? "Sin resultados"}
        </div>
      </Surface>
    );
  }

  return (
    <Surface className={cn("overflow-hidden p-0", className)}>
      <table className="w-full table-fixed">
        <thead className="sticky top-0 bg-slate-50/80 backdrop-blur-sm border-b border-slate-200">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "h-10 text-[11px] uppercase tracking-wider font-mono text-slate-500 px-4",
                  ALIGN_TH[col.align ?? "left"]
                )}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => {
            const key = getRowKey ? getRowKey(row) : rowIdx;
            const accent = rowAccent ? rowAccent(row) : null;
            return (
              <tr
                key={key}
                data-accent={accent ?? undefined}
                className={cn(
                  "h-12 border-b border-slate-100 last:border-0 transition-colors duration-150",
                  onRowClick && "cursor-pointer",
                  accent ? ACCENT_ROW[accent] : onRowClick ? "hover:bg-slate-50" : ""
                )}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((col, colIdx) => (
                  <td
                    key={col.key}
                    className={cn(
                      "px-4 text-sm text-slate-700 truncate max-w-0",
                      ALIGN_TD[col.align ?? "left"]
                    )}
                  >
                    {colIdx === 0 && onRowClick ? (
                      <button
                        className="w-full text-left h-full flex items-center"
                        tabIndex={-1}
                        onClick={(e) => { e.stopPropagation(); onRowClick(row); }}
                      >
                        {col.render(row)}
                      </button>
                    ) : (
                      col.render(row)
                    )}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Surface>
  );
}
