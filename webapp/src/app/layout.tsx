import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Donna - Email Fraud Protection for Billing",
    template: "%s | Donna"
  },
  description: "Advanced email fraud detection and prevention for billing communications. Protect your business with AI-powered analysis and real-time call agent verification.",
  keywords: ["email fraud detection", "billing security", "fraud prevention", "email security", "call verification", "business protection", "AI fraud detection", "payment security"],
  metadataBase: new URL('http://localhost:3000'),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    title: "Donna - Email Fraud Protection for Billing",
    description: "Advanced email fraud detection and prevention for billing communications. Protect your business with AI-powered analysis and real-time call agent verification.",
    siteName: "Donna",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
