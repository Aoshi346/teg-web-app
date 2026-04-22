import * as React from "react"

import { cn } from "@shared/lib/utils"
import {
  Surface,
  SurfaceHeader,
  SurfaceTitle,
  SurfaceDescription,
  SurfaceAction,
  SurfaceContent,
  SurfaceFooter,
  type SurfaceProps,
} from "./Surface"

function Card({ className, ...props }: SurfaceProps) {
  return (
    <Surface
      data-slot="card"
      className={cn("py-6", className)}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceHeader data-slot="card-header" className={className} {...props} />
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceTitle data-slot="card-title" className={className} {...props} />
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceDescription data-slot="card-description" className={className} {...props} />
}

function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceAction data-slot="card-action" className={className} {...props} />
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceContent data-slot="card-content" className={className} {...props} />
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return <SurfaceFooter data-slot="card-footer" className={className} {...props} />
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}
