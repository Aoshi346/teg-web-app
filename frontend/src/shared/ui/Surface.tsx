import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@shared/lib/utils"

const surfaceVariants = cva(
  "relative flex flex-col gap-6 rounded-2xl border border-slate-200 shadow-sm",
  {
    variants: {
      tone: {
        default: "bg-white text-slate-800",
        muted: "bg-slate-50 text-slate-800",
        sunken: "bg-slate-50 text-slate-800 border-transparent shadow-none",
        inverse: "bg-[#011638] text-white border-transparent",
      },
      interactive: {
        true: "cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-[box-shadow,transform] duration-200 focus-within:ring-2 focus-within:ring-primary/40",
        false: "",
      },
    },
    defaultVariants: {
      tone: "default",
      interactive: false,
    },
  }
)

const STATUS_BAR_CLASSES: Record<string, string> = {
  success: "before:absolute before:left-0 before:top-4 before:bottom-4 before:w-[3px] before:rounded-full before:bg-[oklch(0.70_0.15_160)]",
  pending: "before:absolute before:left-0 before:top-4 before:bottom-4 before:w-[3px] before:rounded-full before:bg-[oklch(0.78_0.14_75)]",
  destructive: "before:absolute before:left-0 before:top-4 before:bottom-4 before:w-[3px] before:rounded-full before:bg-[oklch(0.60_0.22_27)]",
}

export interface SurfaceProps
  extends React.ComponentProps<"div">,
    VariantProps<typeof surfaceVariants> {
  status?: "none" | "success" | "pending" | "destructive"
}

function Surface({
  className,
  tone,
  interactive,
  status = "none",
  ...props
}: SurfaceProps) {
  const statusClass = status !== "none" ? STATUS_BAR_CLASSES[status] : ""

  return (
    <div
      data-slot="surface"
      data-status={status !== "none" ? status : undefined}
      className={cn(
        surfaceVariants({ tone, interactive }),
        statusClass,
        className
      )}
      {...props}
    />
  )
}

function SurfaceHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-header"
      className={cn(
        "@container/surface-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=surface-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        className
      )}
      {...props}
    />
  )
}

function SurfaceTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-title"
      className={cn("leading-none font-semibold", className)}
      {...props}
    />
  )
}

function SurfaceDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props}
    />
  )
}

function SurfaceAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className
      )}
      {...props}
    />
  )
}

function SurfaceContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-content"
      className={cn("px-6", className)}
      {...props}
    />
  )
}

function SurfaceFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="surface-footer"
      className={cn("flex items-center px-6 [.border-t]:pt-6", className)}
      {...props}
    />
  )
}

export {
  Surface,
  SurfaceHeader,
  SurfaceTitle,
  SurfaceDescription,
  SurfaceAction,
  SurfaceContent,
  SurfaceFooter,
  surfaceVariants,
}
