import type { Metadata } from "next";
import { Montserrat, Fraunces } from "next/font/google";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { NotificationProvider } from "@shared/ui/NotificationProvider";

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  axes: ["opsz", "SOFT", "WONK"],
  display: "swap",
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
    <html lang="es" className={`${GeistSans.variable} ${GeistMono.variable} ${montserrat.variable} ${fraunces.variable}`}>
      <body className={`${GeistSans.className} antialiased`}>
        <NotificationProvider>{children}</NotificationProvider>
      </body>
    </html>
  );
}
