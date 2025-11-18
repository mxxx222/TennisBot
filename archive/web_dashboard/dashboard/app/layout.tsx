import type { Metadata } from 'next';
import './globals.css';
import ResponsiveLayout from '@/components/ResponsiveLayout';

export const metadata: Metadata = {
  title: 'Betting Dashboard',
  description: 'Responsive betting dashboard with Notion integration',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ResponsiveLayout>{children}</ResponsiveLayout>
      </body>
    </html>
  );
}

