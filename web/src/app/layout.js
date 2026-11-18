import { Inter, Bricolage_Grotesque, Public_Sans } from "next/font/google";
import "./globals.css";
import "./theme.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const display = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-display", display: "swap" });
const text = Public_Sans({ subsets: ["latin"], variable: "--font-text", display: "swap" });

export const metadata = {
  title: "RiskLENS — Diabetes Risk Screening",
  description:
    "Answer 21 questions from the CDC's health survey and get a diabetes risk score with the factors behind it. An educational screening project, not a diagnosis.",
  keywords: "diabetes, risk assessment, health screening, BRFSS, CDC, machine learning",
};

// Runs before first paint: applies the visitor's stored theme choice (if any)
// so the page never flashes the wrong theme (FOUC). When no choice was stored,
// no attribute is set and the CSS media query follows the system preference.
// Keep the storage key in sync with ThemeToggle.js.
const themeInitScript = `
(function () {
  try {
    var t = localStorage.getItem("risklens-theme");
    if (t === "dark" || t === "light") {
      document.documentElement.setAttribute("data-theme", t);
    }
  } catch (e) {}
})();
`;

export default function RootLayout({ children }) {
  return (
    // suppressHydrationWarning: the inline script above may set data-theme on
    // <html> before React hydrates, which is intentional.
    <html
      lang="en"
      className={`${inter.variable} ${display.variable} ${text.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
