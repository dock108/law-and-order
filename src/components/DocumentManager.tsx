'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Reuse DocumentRecord interface (or import if defined centrally)
interface DocumentRecord {
    id: string;
    clientId: string;
    documentType: string;
    fileUrl: string;
    createdAt: string;
}

interface DocumentManagerProps {
    clientId: string;
    initialDocuments: DocumentRecord[];
}

// Simple date formatter (can be imported from dashboard or a shared util)
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: 'numeric', minute: '2-digit'
    });
  } catch { return dateString; }
};

export function DocumentManager({ clientId, initialDocuments = [] }: DocumentManagerProps) {
    const [documents, setDocuments] = useState<DocumentRecord[]>(initialDocuments);
    const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const availableTemplates = ['demand-letter', 'representation-letter']; // Example list

    // Function to generate a new document
    const handleGenerateDocument = async (documentType: string) => {
        setIsLoading(prev => ({ ...prev, [`generate-${documentType}`]: true }));
        setError(null);
        setSuccess(null);
        try {
            const response = await fetch(`/api/clients/${clientId}/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ documentType }),
            });
            const newDoc = await response.json();
            if (!response.ok) {
                throw new Error(newDoc.error || 'Failed to generate document');
            }
            // Add the new document to the list
            setDocuments(prev => [newDoc, ...prev]);
            setSuccess(`Successfully generated ${documentType}.`);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Document generation failed.');
        } finally {
            setIsLoading(prev => ({ ...prev, [`generate-${documentType}`]: false }));
        }
    };

    // Function to get download URL and initiate download
    const handleDownloadDocument = async (documentId: string, filenameHint: string = 'document.pdf') => {
        setIsLoading(prev => ({ ...prev, [`download-${documentId}`]: true }));
        setError(null);
        setSuccess(null);
        try {
            const response = await fetch(`/api/documents/${documentId}/download`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get download URL');
            }
            const downloadUrl = data.downloadUrl;

            // Trigger download
            const link = document.createElement('a');
            link.href = downloadUrl;
            // Add filename hint for the browser's save dialog
            link.setAttribute('download', filenameHint);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link); // Clean up

        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Download failed.');
        } finally {
            setIsLoading(prev => ({ ...prev, [`download-${documentId}`]: false }));
        }
    };

    // Helper to format document type name for display
    const formatDocumentType = (docType: string): string => {
        return docType
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    return (
        <div className="bg-white shadow-md rounded-lg border-2 border-slate-300 overflow-hidden">
            <div className="border-b border-slate-300 px-6 py-4 bg-blue-800 text-white flex justify-between items-center">
                <h2 className="text-2xl font-serif font-bold">Document Management</h2>
            </div>

            <div className="p-6 space-y-6 bg-white">
                {/* Notification Messages */}
                {error && (
                    <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded shadow-sm">
                        <div className="flex items-start">
                            <svg className="h-5 w-5 text-red-600 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <div>
                                <p className="text-sm font-medium text-red-800">{error}</p>
                            </div>
                        </div>
                    </div>
                )}
                
                {success && (
                    <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded shadow-sm">
                        <div className="flex items-start">
                            <svg className="h-5 w-5 text-green-600 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div>
                                <p className="text-sm font-medium text-green-800">{success}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Generate New Document Section */}
                <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 shadow-sm">
                    <h3 className="text-lg font-medium text-blue-900 mb-4 border-b border-blue-200 pb-2">Generate New Document</h3>
                    <p className="text-slate-800 text-sm mb-4">Select a document type to generate a new document for this client. Generated documents will be stored securely and available for download.</p>
                    <div className="flex flex-wrap gap-3 items-center">
                        {availableTemplates.map(template => (
                            <button
                                key={template}
                                onClick={() => handleGenerateDocument(template)}
                                disabled={isLoading[`generate-${template}`]}
                                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white !bg-blue-500 hover:!bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                style={{ backgroundColor: '#3b82f6' }}
                            >
                                {isLoading[`generate-${template}`] ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        {formatDocumentType(template)}
                                    </>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Existing Documents List */}
                <div className="bg-slate-50 p-6 rounded-lg border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-medium text-blue-900 mb-4 border-b border-slate-200 pb-2">Existing Documents</h3>
                    
                    {documents.length === 0 ? (
                        <div className="text-center bg-white rounded-lg py-12 px-6 border border-slate-200 shadow-inner">
                            <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <h3 className="mt-2 text-sm font-medium text-slate-900">No documents</h3>
                            <p className="mt-1 text-sm text-slate-600">Get started by creating a new document.</p>
                        </div>
                    ) : (
                        <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
                            <ul className="divide-y divide-slate-200">
                                {documents.map(doc => (
                                    <li key={doc.id} className="p-4 hover:bg-blue-50 transition-colors">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10 bg-blue-100 text-blue-800 rounded-lg flex items-center justify-center border border-blue-200">
                                                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                    </svg>
                                                </div>
                                                <div className="ml-4">
                                                    <h4 className="text-sm font-medium text-slate-900">{formatDocumentType(doc.documentType)}</h4>
                                                    <p className="text-sm text-slate-600">Generated: {formatDate(doc.createdAt)}</p>
                                                </div>
                                            </div>
                                            <div className="flex space-x-2">
                                                <button
                                                    onClick={() => handleDownloadDocument(doc.id, `${doc.documentType}-${clientId.substring(0, 8)}.pdf`)}
                                                    disabled={isLoading[`download-${doc.id}`]}
                                                    className="inline-flex items-center px-3 py-1.5 border border-transparent rounded-md shadow-sm text-xs font-medium text-white !bg-blue-500 hover:!bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                    style={{ backgroundColor: '#3b82f6' }}
                                                >
                                                    {isLoading[`download-${doc.id}`] ? (
                                                        <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                        </svg>
                                                    ) : (
                                                        <>
                                                            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                            </svg>
                                                            Download
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
} 