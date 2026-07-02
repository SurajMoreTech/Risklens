import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata = {
  title: "RiskLens — Diabetes Risk Screening",
  description:
    "Know your diabetes risk in 5 minutes — no blood test required. Clinically validated screening using CDC health indicators with AI-powered risk assessment.",
  keywords: "diabetes, risk assessment, health screening, BRFSS, CDC, machine learning",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>{children}</body>
    </html>
  );
}
