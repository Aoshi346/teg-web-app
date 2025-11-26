"use client";

import React from "react";

export default function TesisLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
