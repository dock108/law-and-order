import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Clients - Law & Order",
  description: "Law & Order client management",
};

export default function ClientsLayout({
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