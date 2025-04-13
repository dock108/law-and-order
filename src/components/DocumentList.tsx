'use client';

import React, { useState } from 'react';
import { Prisma } from '@prisma/client'; // Import Prisma types for Document

// Define the expected structure for a document passed as a prop
// Use Prisma namespace to avoid conflicts if you have a global Document type
type Document = Prisma.DocumentGetPayload<{
    select: { id: true, documentType: true, fileUrl: true, createdAt: true, updatedAt: true }
}>;

interface DocumentListProps {
  documents: Document[];
  clientId: string;
}

export default function DocumentList({ documents, clientId }: DocumentListProps) {
  const [regenState, setRegenState] = useState<Record<string, { loading: boolean; error: string | null; success: string | null }>>({});

  const handleRegenerate = async (document: Document) => {
    const docId = document.id;
    setRegenState(prev => ({ 
        ...prev, 
        [docId]: { loading: true, error: null, success: null }
    }));

    try {
      const response = await fetch('/api/documents/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentId: docId,
          clientId: clientId,
          documentType: document.documentType,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to regenerate document');
      }

      setRegenState(prev => ({ 
          ...prev, 
          [docId]: { loading: false, error: null, success: result.message || 'Document regenerated!' }
      }));
      // Optionally: Add a small delay then clear the success message
      setTimeout(() => setRegenState(prev => ({ ...prev, [docId]: { ...prev[docId], success: null } })), 3000);

    } catch (error: unknown) {
      console.error("Regeneration failed:", error);
      setRegenState(prev => ({ 
          ...prev, 
          [docId]: { loading: false, error: error instanceof Error ? error.message : 'An unknown error occurred', success: null }
      }));
    }
  };

  const formatDate = (dateString: string | Date): string => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
    } catch {
      return 'Invalid Date';
    }
  };

  if (!documents || documents.length === 0) {
    return <p className="text-sm text-gray-500 italic">No documents found for this client yet.</p>;
  }

  return (
    <div className="space-y-3">
      {documents.map((doc) => {
        const state = regenState[doc.id] || { loading: false, error: null, success: null };
        return (
          <div key={doc.id} className="p-4 bg-white rounded-md border border-gray-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-3 sm:space-y-0">
            <div className="flex-1 mr-4">
              <p className="text-sm font-medium text-gray-900">{doc.documentType}</p>
              <p className="text-xs text-gray-500">
                Created: {formatDate(doc.createdAt)} | Updated: {formatDate(doc.updatedAt)}
              </p>
              {/* Display feedback messages */} 
              {state.error && <p className="text-xs text-red-600 mt-1">Error: {state.error}</p>}
              {state.success && <p className="text-xs text-green-600 mt-1">{state.success}</p>}
            </div>
            <div className="flex space-x-2 flex-shrink-0">
              {/* Download Button (uses separate endpoint) */}
              <a
                href={`/api/documents/${doc.id}/download`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-xs font-medium text-center text-white bg-blue-600 rounded hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 transition duration-150"
              >
                Download
              </a>
              {/* Regenerate Button */}
              <button
                type="button"
                onClick={() => handleRegenerate(doc)}
                disabled={state.loading}
                className={`px-3 py-1.5 text-xs font-medium text-center text-white rounded focus:ring-4 focus:outline-none transition duration-150 ${state.loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-300'}`}
              >
                {state.loading ? 'Regenerating...' : 'Re-create Doc'}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
} 