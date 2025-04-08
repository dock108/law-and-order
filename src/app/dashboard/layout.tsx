import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard - Law & Order",
  description: "Law & Order management dashboard",
};

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-grow">
        {children}
      </main>
    </div>
  );
} 