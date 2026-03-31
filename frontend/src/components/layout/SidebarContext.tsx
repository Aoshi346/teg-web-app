"use client";

import React, { createContext, useContext } from "react";

export interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (v: boolean) => void;
  toggleCollapse: () => void;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
  toggleMobile: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const SidebarProvider = ({
  children,
  value,
}: {
  children: React.ReactNode;
  value: SidebarContextType;
}) => {
  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
};

export const useSidebar = (): SidebarContextType => {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return ctx;
};

export default SidebarContext;
