import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "New Client - Law & Order",
  description: "Add a new client to Law & Order",
};

export default function NewClientLayout({
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