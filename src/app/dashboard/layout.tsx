"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { isAuthenticated } from "@/features/auth/clientAuth";
import LoginLoading from "@/components/ui/LoginLoading";
import RouteLoading from "@/components/ui/RouteLoading";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(true);
  const hasCheckedAuthRef = useRef(false);

  useEffect(() => {
    // Only check auth once on mount
    if (hasCheckedAuthRef.current) return;
    
    // Check auth synchronously for instant response
    const authenticated = isAuthenticated();
    if (!authenticated) {
      router.push("/");
    } else {
      // Set immediately - no delay
      setIsAuthenticating(false);
      hasCheckedAuthRef.current = true;
    }
  }, [router]);

  const handleSidebarCollapse = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  const handleMobileSidebarToggle = useCallback(() => {
    setIsMobileSidebarOpen((prev) => !prev);
  }, []);

  // Close mobile sidebar when route changes
  useEffect(() => {
    setIsMobileSidebarOpen(false);
  }, [pathname]);

  if (isAuthenticating) {
    return <LoginLoading visible={true} message="Verificando sesión..." />;
  }

  return (
    <>
      <RouteLoading />
      <div className="min-h-screen w-full flex bg-gray-100">
        <Sidebar 
          isCollapsed={isSidebarCollapsed} 
          setIsCollapsed={setIsSidebarCollapsed} 
          mobileOpen={isMobileSidebarOpen} 
          setMobileOpen={setIsMobileSidebarOpen} 
        />
        <div className="flex-1 flex flex-col overflow-hidden transition-all duration-300">
          {/* Pass sidebar state down to children (pages) so they can use it for the header */}
          {React.isValidElement(children)
            ? React.cloneElement(children, {
                handleSidebarCollapse, 
                handleMobileSidebarToggle, 
                isSidebarCollapsed, 
                isMobileSidebarOpen
              } as any)
            : children}
        </div>
      </div>
    </>
  );
}

