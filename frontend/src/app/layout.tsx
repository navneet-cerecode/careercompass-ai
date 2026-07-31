import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.CAREERCOMPASS_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "CareerCompass AI — Move with clarity",
  description:
    "Explainable career intelligence that connects your real experience to the right opportunities.",
  openGraph: {
    title: "CareerCompass AI — Move with clarity",
    description: "Explainable career intelligence, grounded in your story.",
    images: [{ url: "/og.png", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CareerCompass AI — Move with clarity",
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
      <body>{children}</body>
    </html>
  );
}
