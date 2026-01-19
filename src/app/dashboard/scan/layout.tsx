"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUserRole } from "@/features/auth/clientAuth";

export default function ScanLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const [role, setRole] = useState<string | null>(null);

    useEffect(() => {
        // Check role on mount
        const currentRole = getUserRole();
        setRole(currentRole);

        if (currentRole === "Admin") {
            // Admin not allowed in Scan module
            router.push("/dashboard");
        }
    }, [router]);

    if (role === "Admin") {
        return null; // Or a loading spinner/access denied message while redirecting
    }

    return <>{children}</>;
}
