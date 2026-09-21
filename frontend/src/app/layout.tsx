import { Archivo, Martian_Mono } from "next/font/google";
import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-archivo",
});

const martian = Martian_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-martian",
});

export const metadata = { title: "NextShift — Operations Console" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${martian.variable}`}>
      <body>{children}</body>
    </html>
  );
}
