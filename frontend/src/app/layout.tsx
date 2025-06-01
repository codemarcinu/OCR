import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import MainLayout from '@/components/layout/MainLayout';

const inter = Inter({ subsets: ['latin', 'latin-ext'] });

export const metadata: Metadata = {
  title: 'OCR Manager',
  description: 'Personal finance and pantry management system with OCR capabilities',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body className={inter.className}>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
} 