import Link from 'next/link';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { redirect } from 'next/navigation';
import { headers } from 'next/headers'; // Import headers to pass cookies
import { Prisma } from '@prisma/client'; // Import Prisma types for Task
import TaskList from '@/components/TaskList'; // Import the new client component
import AddClientButton from '@/components/AddClientButton'; // Import the new button component

// Define interfaces for stronger typing
interface Task {
  id: string;
  description: string;
  dueDate: string | null; // Dates are often serialized as strings
  status: string;
  createdAt: string;
  automationType?: string | null;
  requiresDocs?: boolean | null;
  automationConfig?: string | null;
}

interface Client {
  id: string;
  name: string;
  email: string;
  onboardedAt: string; // API returns string, might need parsing if Date object needed
  tasks: Task[]; // Include tasks in the client type
}

// Reuse existing formatDate or create a new one if different format is needed
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    // Example: Short date format
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
    });
  } catch (e) {
    console.error("Error parsing date:", dateString, e);
    return dateString; 
  }
};

// Function to determine styling for task status
const getStatusBadge = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'overdue': // Assume overdue status might be set by a background job or check
      return 'bg-red-100 text-red-800';
    case 'in progress':
      return 'bg-yellow-100 text-yellow-800';
    case 'pending':
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Function to check if a task is overdue
const isTaskOverdue = (dueDateString: string | null, status: string): boolean => {
    if (!dueDateString || status.toLowerCase() === 'completed') {
        return false;
    }
    try {
        const dueDate = new Date(dueDateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Compare dates only
        return dueDate < today;
    } catch (e) {
        return false;
    }
};

// Updated function to fetch clients with their tasks
// Now accepts cookie string as an argument
async function getClientsWithTasks(cookie: string): Promise<Client[]> {
  const session = await getServerSession(authOptions);
  if (!session) {
    // Redirect should ideally happen before calling this, 
    // but kept here as a safeguard. Consider moving session check outside.
    redirect('/api/auth/signin');
  }

  const apiUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/api/clients?includeTasks=true`;

  try {
    console.log(`Fetching clients with tasks from: ${apiUrl}`);
    const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
            // Use the passed cookie string
            'Cookie': cookie, 
            'Content-Type': 'application/json',
        },
        cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to fetch clients with tasks: ${response.status} ${response.statusText}`, errorText);
      throw new Error(`Failed to fetch clients with tasks. Status: ${response.status}`);
    }

    const clients: Client[] = await response.json();
    console.log(`Fetched ${clients.length} clients with task data.`);
    return clients;

  } catch (error) {
    console.error('Error fetching clients with tasks:', error);
    return [];
  }
}

// Make the page component async
export default async function DashboardPage() {
  // Perform session check at the top level if desired
  const session = await getServerSession(authOptions);
  if (!session) { redirect('/api/auth/signin'); }

  // Read cookie at the top level of the Server Component
  const cookie = headers().get('cookie') || '';
  
  // Fetch clients with tasks, passing the cookie
  const clients = await getClientsWithTasks(cookie);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Letterhead integrated into the dashboard directly */}
      <div className="mb-6 bg-white shadow-lg rounded-lg overflow-hidden">
        <iframe
          src="/letterhead.pdf#toolbar=0&navpanes=0&scrollbar=0"
          width="100%"
          height="180"
          className="border-0"
        />
      </div>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Client Dashboard</h1>
        <AddClientButton />
      </div>

      {/* Client List Table (Simplified - focus shifts to clients with tasks) */}
      {clients.map((client) => (
          <div key={client.id} className="bg-white shadow-lg rounded-lg mb-8 overflow-hidden border border-gray-200">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-700">
                <Link href={`/clients/${client.id}`} className="hover:text-blue-600 transition duration-150">
                  {client.name}
                </Link>
              </h2>
              <span className="text-sm text-gray-500">Onboarded: {formatDate(client.onboardedAt)}</span>
            </div>
            
            <div className="p-6">
                <h3 className="text-lg font-medium text-gray-600 mb-4">Tasks</h3>
                <TaskList initialTasks={client.tasks || []} clientId={client.id} />
            </div>

            <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 text-right">
                <Link href={`/clients/${client.id}`} className="text-sm text-indigo-600 hover:text-indigo-800 font-medium transition duration-150">
                    View Full Details & Documents →
                </Link>
            </div>
          </div>
      ))}

      {clients.length === 0 && (
           <div className="text-center py-10 bg-white shadow rounded-lg">
                <p className="text-gray-500">No clients found.</p>
           </div>
      )}
    </div>
  );
} 