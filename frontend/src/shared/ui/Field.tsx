import * as React from "react"

import { cn } from "@shared/lib/utils"

export interface FieldProps {
  label?: string
  description?: string
  error?: string
  required?: boolean
  className?: string
  children: React.ReactElement<React.HTMLAttributes<HTMLElement> & { id?: string; "aria-invalid"?: boolean | "true" | "false" | "grammar" | "spelling"; "aria-describedby"?: string }>
}

function Field({
  label,
  description,
  error,
  required,
  className,
  children,
}: FieldProps) {
  const id = React.useId()
  const controlId = `field-control-${id}`
  const descriptionId = description ? `field-desc-${id}` : undefined
  const errorId = error ? `field-error-${id}` : undefined

  const ariaDescribedBy = [descriptionId, errorId].filter(Boolean).join(" ") || undefined

  const control = React.cloneElement(children, {
    id: children.props.id ?? controlId,
    "aria-invalid": error ? ("true" as const) : children.props["aria-invalid"],
    "aria-describedby": ariaDescribedBy,
  })

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      {label && (
        <label
          htmlFor={children.props.id ?? controlId}
          className="text-sm font-medium text-slate-700"
        >
          {label}
          {required && (
            <span className="ml-1 text-destructive" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}
      {control}
      {description && !error && (
        <p id={descriptionId} className="text-xs text-slate-500">
          {description}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export { Field }
