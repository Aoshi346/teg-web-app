import type { Metadata } from "next";
import { Montserrat } from "next/font/google";
import "./globals.css";
import { NotificationProvider } from "@/components/ui/NotificationProvider";

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
});

export const metadata: Metadata = {
  title: "TesisFar",
  description: "TesisFar - Evaluador de Trabajos Especiales de Grado",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${montserrat.className} antialiased`}>
        <NotificationProvider>{children}</NotificationProvider>
      </body>
    </html>
  );
}
