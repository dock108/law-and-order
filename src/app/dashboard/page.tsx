import Link from 'next/link';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { redirect } from 'next/navigation';
import { headers } from 'next/headers'; // Import headers to pass cookies

interface Client {
  id: string;
  name: string;
  email: string;
  onboardedAt: string; // API returns string, might need parsing if Date object needed
  // Add other fields if needed from your API response
}

// Simple date formatter (adjust as needed for string date from API)
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch (e) {
      console.error("Error parsing date:", dateString, e);
      return dateString; // Return original string if parsing fails
  }
};

// Function to fetch clients server-side
async function getClients(): Promise<Client[]> {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect('/api/auth/signin');
  }

  // Construct the full API URL for server-side fetch
  const apiUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/api/clients`;

  try {
    console.log(`Fetching clients from: ${apiUrl}`);
    const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
            // Forward necessary headers, especially cookies for session authentication within API route
            // Using next/headers allows access to incoming request headers
            'Cookie': headers().get('cookie') || '',
            'Content-Type': 'application/json',
        },
        cache: 'no-store', // Ensure fresh data is fetched each time
    });

    if (!response.ok) {
      // Log more details on fetch failure
      const errorText = await response.text();
      console.error(`Failed to fetch clients: ${response.status} ${response.statusText}`, errorText);
      throw new Error(`Failed to fetch clients. Status: ${response.status}`);
    }

    const clients: Client[] = await response.json();
    console.log(`Fetched ${clients.length} clients.`);
    return clients;

  } catch (error) {
    console.error('Error fetching clients:', error);
    // Return empty array or re-throw, depending on desired error handling
    return [];
  }
}

export default async function DashboardPage() {
  // Fetch clients on the server
  const clients = await getClients();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Client Dashboard</h1>
        <Link href="/new-client">
          <span className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out cursor-pointer">
            Add New Client
          </span>
        </Link>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full leading-normal">
          <thead>
            <tr className="bg-gray-100 text-gray-600 uppercase text-sm leading-normal">
              <th className="py-3 px-6 text-left">Name</th>
              <th className="py-3 px-6 text-left">Email</th>
              <th className="py-3 px-6 text-left">Onboarded Date</th>
              <th className="py-3 px-6 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="text-gray-700 text-sm">
            {clients.map((client) => (
              <tr key={client.id} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="py-3 px-6 text-left whitespace-nowrap">
                   {/* Link the name to a future detail page */}
                   <Link href={`/clients/${client.id}`} className="text-blue-600 hover:underline">
                     {client.name}
                   </Link>
                </td>
                <td className="py-3 px-6 text-left">{client.email}</td>
                <td className="py-3 px-6 text-left">{formatDate(client.onboardedAt)}</td>
                <td className="py-3 px-6 text-left">
                    {/* Link to the client detail page which has the DocumentManager */}
                    <Link href={`/clients/${client.id}`} className="text-indigo-600 hover:text-indigo-900">
                        View Docs
                    </Link>
                </td>
              </tr>
            ))}
            {clients.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 px-6 text-center text-gray-500">
                  No clients found. Add one?
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
} 