import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@shared/lib/utils"

const trackVariants = cva(
  "inline-flex items-center rounded-lg border border-slate-200 bg-white p-1 gap-1",
  {
    variants: {
      fullWidth: {
        true: "flex w-full",
        false: "inline-flex",
      },
    },
    defaultVariants: {
      fullWidth: false,
    },
  }
)

const optionVariants = cva(
  "relative flex items-center justify-center gap-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer select-none border",
  {
    variants: {
      size: {
        sm: "h-7 px-2.5 text-xs",
        default: "h-8 px-3",
        lg: "h-10 px-4",
      },
      selected: {
        true: "bg-primary/10 text-primary border-primary",
        false: "bg-transparent text-slate-600 border-transparent hover:bg-slate-50 hover:text-slate-900",
      },
      fullWidth: {
        true: "flex-1",
        false: "",
      },
    },
    defaultVariants: {
      size: "default",
      selected: false,
      fullWidth: false,
    },
  }
)

export interface SegmentedControlOption {
  value: string
  label: string
  icon?: React.ReactNode
}

export interface SegmentedControlProps extends VariantProps<typeof trackVariants> {
  value: string
  onChange: (value: string) => void
  options: SegmentedControlOption[]
  size?: "sm" | "default" | "lg"
  fullWidth?: boolean
  className?: string
  "aria-label"?: string
  "aria-labelledby"?: string
}

function SegmentedControl({
  value,
  onChange,
  options,
  size = "default",
  fullWidth = false,
  className,
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledby,
}: SegmentedControlProps) {
  const selectedIndex = options.findIndex((o) => o.value === value)

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const current = options.findIndex((o) => o.value === value)

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault()
      const next = (current + 1) % options.length
      onChange(options[next].value)
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault()
      const prev = (current - 1 + options.length) % options.length
      onChange(options[prev].value)
    } else if (event.key === "Home") {
      event.preventDefault()
      onChange(options[0].value)
    } else if (event.key === "End") {
      event.preventDefault()
      onChange(options[options.length - 1].value)
    }
  }

  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledby}
      onKeyDown={handleKeyDown}
      className={cn(trackVariants({ fullWidth }), className)}
    >
      {options.map((option, index) => {
        const isSelected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            tabIndex={isSelected ? 0 : selectedIndex === -1 && index === 0 ? 0 : -1}
            onClick={() => onChange(option.value)}
            className={cn(
              optionVariants({ size, selected: isSelected, fullWidth })
            )}
          >
            {option.icon && <span className="shrink-0">{option.icon}</span>}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

export { SegmentedControl }
