import React from 'react';
import { getServerSession } from 'next-auth/next';
import { redirect } from 'next/navigation';
import { headers } from 'next/headers';
import Link from 'next/link';
// import { DocumentManager } from '@/components/DocumentManager'; // Assuming DocumentList replaces this
import { TaskList } from '@/components/TaskList';
import DocumentList from '@/components/DocumentList'; // Import the new component
import { Prisma } from '@prisma/client'; // Import Prisma for types
import DeleteClientSection from '@/components/DeleteClientSection'; // Import the delete section

// Define Document type based on expected Prisma payload
type Document = Prisma.DocumentGetPayload<{
    select: { id: true, documentType: true, fileUrl: true, createdAt: true, updatedAt: true }
}>;

// Define Task type based on expected Prisma payload
type Task = Prisma.TaskGetPayload<{
    select: { id: true, description: true, dueDate: true, status: true, createdAt: true, automationType: true, requiresDocs: true, automationConfig: true }
}>;

// Define ClientDetails with relations included
interface ClientDetails extends Prisma.ClientGetPayload<{
    include: { tasks: true, documents: true } 
}> {
    // Ensure tasks and documents are potentially included (even if empty array)
    tasks?: Task[];
    documents?: Document[];
}

// Removed separate DocumentRecord interface

interface RouteParams {
  params: { clientId: string };
}

// Updated fetch function to include both tasks and documents
async function getClientDetailsWithRelations(clientId: string, cookie: string): Promise<ClientDetails | null> {
    const apiUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/api/clients/${clientId}?includeTasks=true&includeDocuments=true`; 
    console.log(`Fetching client ${clientId} details with relations from ${apiUrl}`);
    try {
        const response = await fetch(apiUrl, { headers: { 'Cookie': cookie, 'Cache-Control': 'no-store' } }); // Add no-store
        if (!response.ok) {
            if (response.status === 404) return null;
            console.error(`Failed to fetch client ${clientId} with relations: ${response.status}`);
            throw new Error(`Failed to fetch client with relations. Status: ${response.status}`);
        }
        const clientData: ClientDetails = await response.json();
        // Ensure arrays exist
        clientData.tasks = clientData.tasks || [];
        clientData.documents = clientData.documents || [];
        return clientData;
    } catch (error) {
        console.error(`Error fetching client ${clientId} with relations:`, error);
        return null; // Or re-throw
    }
}

// Removed getClientDocuments as it's included above

// Format date for display (keep existing)
function formatDate(dateString: string | Date | null | undefined): string {
    if (!dateString) return 'Not provided';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch {
        return 'Invalid date';
    }
}

// Format currency for display (keep existing)
function formatCurrency(amount: number | null | undefined): string {
    if (amount === null || amount === undefined) return 'Not provided';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount);
}

export default async function ClientDetailPage({ params }: RouteParams) {
    const session = await getServerSession();
    if (!session) {
        redirect('/api/auth/signin');
    }

    const cookie = headers().get('cookie') || '';
    const { clientId } = params;
    
    // Use the combined fetch function
    const client = await getClientDetailsWithRelations(clientId, cookie);
    // const initialDocuments = await getClientDocuments(clientId, cookie); // Removed

    if (!client) {
        return (
            <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center p-4">
                <div className="bg-white shadow-lg rounded-lg p-8 max-w-md w-full text-center">
                    <svg className="h-16 w-16 text-red-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <h1 className="text-2xl font-serif font-bold text-slate-800 mb-2">Client Not Found</h1>
                    <p className="text-slate-600 mb-6">The requested client information could not be located.</p>
                    <Link href="/dashboard" className="inline-flex items-center px-4 py-2 !bg-blue-500 text-white text-sm font-medium rounded-md hover:!bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400" style={{ backgroundColor: '#3b82f6' }}>
                        <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Return to Dashboard
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-100 py-8">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Breadcrumb Navigation */}
                <nav className="flex mb-4 bg-white px-4 py-2 rounded-md shadow-sm border border-slate-200" aria-label="Breadcrumb">
                    <ol className="flex items-center space-x-2 text-sm">
                        <li>
                            <Link href="/dashboard" className="text-blue-800 hover:text-blue-900 font-medium">Dashboard</Link>
                        </li>
                        <li className="flex items-center">
                            <svg className="h-4 w-4 text-slate-400 mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                            </svg>
                            <span className="text-slate-800 font-medium" aria-current="page">Client Details</span>
                        </li>
                    </ol>
                </nav>

                {/* Client Details Heading Outside Card */}
                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-2xl font-serif font-bold text-slate-800">Client Information</h1>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-900 border border-blue-200">
                        Active Client
                    </span>
                </div>

                {/* Client Information Section */}
                <div className="mb-8">
                    <div className="bg-white shadow-md rounded-lg border-2 border-slate-300 overflow-hidden">
                        <div className="p-6 bg-white">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm">
                                    <h2 className="text-lg font-medium text-blue-900 mb-4 border-b pb-2 border-slate-200">Personal Details</h2>
                                    <div className="space-y-3">
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Full Name</p>
                                            <p className="text-slate-900 font-medium">{client.name}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Email Address</p>
                                            <p className="text-slate-900">{client.email}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Phone Number</p>
                                            <p className="text-slate-900">{client.phone || 'Not provided'}</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm">
                                    <h2 className="text-lg font-medium text-blue-900 mb-4 border-b pb-2 border-slate-200">Case Information</h2>
                                    <div className="space-y-3">
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Incident Date</p>
                                            <p className="text-slate-900">{formatDate(client.incidentDate)}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Location</p>
                                            <p className="text-slate-900">{client.location || 'Not provided'}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Insurance Company</p>
                                            <p className="text-slate-900">{client.insuranceCompany || 'Not provided'}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-600">Medical Expenses</p>
                                            <p className="text-slate-900 font-medium">{client.medicalExpenses ? formatCurrency(client.medicalExpenses) : 'Not provided'}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm">
                                <h2 className="text-lg font-medium text-blue-900 mb-4 border-b pb-2 border-slate-200">Case Classification</h2>
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-sm font-medium text-slate-600">Case Type</p>
                                        <p className="text-slate-900 font-medium">{client.caseType || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-600">Verbal Quality</p>
                                        <p className="text-slate-900 font-medium">{client.verbalQuality || 'N/A'}</p>
                                    </div>
                                </div>
                            </div>
                            
                            {client.injuryDetails && (
                                <div className="mt-6 bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm">
                                    <h2 className="text-lg font-medium text-blue-900 mb-4 border-b pb-2 border-slate-200">Injury Details</h2>
                                    <div className="bg-white p-4 rounded-md border border-slate-200">
                                        <p className="text-slate-900 whitespace-pre-line">{client.injuryDetails}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Tasks Section */}
                <div className="mb-8">
                    <h2 className="text-xl font-serif font-bold text-slate-800 mb-4">Tasks</h2>
                    <div className="bg-white shadow-md rounded-lg border border-slate-200 p-6">
                        <TaskList 
                            initialTasks={client.tasks || []} 
                            clientId={client.id}
                        />
                    </div>
                </div>

                {/* Documents Section - Using new DocumentList component */}
                <div className="mb-8">
                    <h2 className="text-xl font-serif font-bold text-slate-800 mb-4">Documents</h2>
                    <div className="bg-white shadow-md rounded-lg border border-slate-200 p-6">
                        <DocumentList 
                            documents={client.documents || []} 
                            clientId={client.id} 
                        />
                    </div>
                </div>

                {/* --- Delete Client Section --- */}
                <DeleteClientSection 
                    clientId={client.id} 
                    clientName={client.name} 
                />
            </div>
        </div>
    );
} 