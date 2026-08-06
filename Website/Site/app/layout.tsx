import type { Metadata } from "next";
import { headers } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") ?? "loopnopalsolutions.xyz";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "https";
  const origin = `${protocol}://${host}`;

  return {
    title: "Loop Nopal Solutions | Movilidad urbana simulada",
    description:
      "Simulacion semaforica, lectura de congestion y prototipos interactivos para movilidad urbana en Queretaro.",
    openGraph: {
      title: "Loop Nopal Solutions",
      description: "Movilidad urbana, medida y simulada.",
      type: "website",
      locale: "es_MX",
      images: [{ url: `${origin}/og.png`, width: 1680, height: 935 }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Loop Nopal Solutions",
      description: "Movilidad urbana, medida y simulada.",
      images: [`${origin}/og.png`],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-MX">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
