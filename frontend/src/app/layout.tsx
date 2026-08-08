import type { Metadata } from "next";
import { Source_Serif_4 } from "next/font/google";
import "./globals.css";

const editorial = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-editorial",
});

const siteUrl =
  process.env.SOLARAHIRE_SITE_URL ??
  process.env.CAREERCOMPASS_SITE_URL ??
  "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Solara Hire — Move with clarity",
  description:
    "Explainable career intelligence that connects your real experience to the right opportunities.",
  openGraph: {
    title: "Solara Hire — Move with clarity",
    description: "Explainable career intelligence, grounded in your story.",
    images: [{ url: "/og.png", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Solara Hire — Move with clarity",
    description: "Explainable career intelligence, grounded in your story.",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={editorial.variable}>{children}</body>
    </html>
  );
}
