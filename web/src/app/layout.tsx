import type { Metadata } from "next";
import { Syne, Space_Mono, Crimson_Pro } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-space-mono",
  display: "swap",
});

const crimsonPro = Crimson_Pro({
  subsets: ["latin"],
  variable: "--font-crimson-pro",
  display: "swap",
});

export const metadata: Metadata = {
  title: "APRIORI MATCH — Know Before You Commit",
  description:
    "AI-powered relationship compatibility prediction. We simulate 100+ relationship scenarios using Theory of Mind and Monte Carlo analysis to predict long-term compatibility.",
  openGraph: {
    title: "APRIORI MATCH — Know Before You Commit",
    description:
      "AI-powered relationship compatibility prediction using recursive Theory of Mind.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider appearance={{ baseTheme: dark }}>
      <html lang="en" className="dark">
        <body
          className={`${syne.variable} ${spaceMono.variable} ${crimsonPro.variable} font-sans antialiased bg-[#020408] text-[#e8f4ff]`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
