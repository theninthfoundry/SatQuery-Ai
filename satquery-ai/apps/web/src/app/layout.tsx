import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SatQuery AI — Multimodal Remote Sensing Assistant',
  description: 'Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-space-950 text-slate-100 antialiased selection:bg-satblue-500/20 selection:text-satblue-300">
        {children}
      </body>
    </html>
  );
}
