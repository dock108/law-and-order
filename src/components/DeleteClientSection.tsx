'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

interface DeleteClientSectionProps {
  clientId: string;
  clientName: string;
}

export default function DeleteClientSection({ clientId, clientName }: DeleteClientSectionProps) {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [confirmationText, setConfirmationText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Define the exact text required for confirmation
  const requiredConfirmation = "delete"; 

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => {
    setIsModalOpen(false);
    setConfirmationText(''); // Reset confirmation on close
    setError(null); // Reset error on close
    setIsLoading(false);
  };

  const handleDelete = async () => {
    if (confirmationText !== requiredConfirmation) {
      setError(`Please type "${requiredConfirmation}" to confirm.`);
      return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/clients/${clientId}`, {
        method: 'DELETE',
      });

      if (response.status === 204) {
        // Success (No Content)
        console.log(`Client ${clientId} deleted successfully.`);
        // Redirect to dashboard after successful deletion
        router.push('/dashboard'); 
        router.refresh(); // Force refresh data on dashboard if needed
      } else {
        // Handle other potential errors (e.g., 404, 500)
        const errorData = await response.json().catch(() => ({ error: 'Failed to delete client. Unknown error.' }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
    } catch (err: unknown) {
      console.error("Failed to delete client:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred during deletion.");
      setIsLoading(false);
    }
    // Don't automatically close modal on error
  };

  return (
    <div className="mt-8 p-6 bg-red-50 border-2 border-dashed border-red-400 rounded-lg">
      <h2 className="text-lg font-semibold text-red-800">Danger Zone</h2>
      <p className="text-sm text-red-700 mt-1 mb-4">
        Deleting this client will permanently remove all associated data, including tasks and documents. This action cannot be undone.
      </p>
      <button
        type="button"
        onClick={openModal}
        className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out shadow-md"
      >
        Delete Client
      </button>

      {/* Confirmation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-red-700 mb-4">Confirm Deletion</h3>
            <p className="text-sm text-gray-700 mb-4">
              This action is irreversible. To confirm permanent deletion of client 
              <strong className="text-gray-900"> {clientName} </strong> 
              and all related data, please type 
              <strong className="text-red-600"> {requiredConfirmation} </strong> 
              into the box below.
            </p>
            
            <input
              type="text"
              value={confirmationText}
              onChange={(e) => setConfirmationText(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-4 border-red-300 focus:border-red-500 focus:ring-red-500"
              placeholder={`Type "${requiredConfirmation}" here`}
            />
            
            {error && (
              <p className="text-xs text-red-600 mb-3">Error: {error}</p>
            )}
            
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={closeModal}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded transition duration-150 ease-in-out"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={confirmationText !== requiredConfirmation || isLoading}
                className={`font-bold py-2 px-4 rounded transition duration-150 ease-in-out shadow-md ${ 
                  (confirmationText !== requiredConfirmation || isLoading)
                    ? 'bg-red-300 text-white cursor-not-allowed'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
              >
                {isLoading ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 