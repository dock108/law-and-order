'use client';

import { useState, useRef, type ChangeEvent, type FormEvent } from 'react';

export default function DocModifierPage() {
  const [originalDocument, setOriginalDocument] = useState<string>('');
  const [instruction, setInstruction] = useState<string>('');
  const [modifiedDocument, setModifiedDocument] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file selection
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check for allowed file types (optional but recommended)
      if (file.type === 'text/plain' || file.type === 'text/markdown') {
        const reader = new FileReader();
        reader.onload = (loadEvent) => {
          const content = loadEvent.target?.result as string;
          setOriginalDocument(content);
          setError(null); // Clear previous errors
        };
        reader.onerror = () => {
          setError('Failed to read the selected file.');
        };
        reader.readAsText(file);
      } else {
        setError('Invalid file type. Please upload a .txt or .md file.');
      }
    }
    // Reset file input value to allow re-uploading the same file
    e.target.value = '';
  };

  // Trigger hidden file input click
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setModifiedDocument(null);

    if (!originalDocument.trim() || !instruction.trim()) {
      setError('Please provide both document content and modification instructions.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/docs/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ document: originalDocument, instruction }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`);
      }

      if (result.modifiedDocument) {
        setModifiedDocument(result.modifiedDocument);
      } else {
        throw new Error('API did not return modified document content.');
      }
    } catch (err: any) {
      console.error('Modification request failed:', err);
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">AI Document Modifier</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Document Input Area */}
        <div>
          <label htmlFor="documentInput" className="block text-sm font-medium text-gray-700 mb-1">
            Document Content (Paste here or Upload .txt/.md file)
          </label>
          <div className="mt-1">
            <textarea
              id="documentInput"
              name="documentInput"
              rows={15}
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
              placeholder="Paste your document content here..."
              value={originalDocument}
              onChange={(e) => setOriginalDocument(e.target.value)}
            />
          </div>
          <div className="mt-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".txt,.md,text/plain,text/markdown"
              className="hidden" // Hide the default file input
            />
            <button
              type="button"
              onClick={handleUploadClick}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Upload File (.txt, .md)
            </button>
          </div>
        </div>

        {/* Modification Instruction Input */}
        <div>
          <label htmlFor="instructionInput" className="block text-sm font-medium text-gray-700 mb-1">
            Modification Instructions
          </label>
          <input
            type="text"
            id="instructionInput"
            name="instructionInput"
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
            placeholder="e.g., Make the tone more assertive, clarify section 3..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            required
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading}
          >
            {isLoading ? 'Modifying...' : 'Modify Document with AI'}
          </button>
        </div>
      </form>

      {/* Modified Document Preview Area */}
      {modifiedDocument && (
        <div className="mt-8 pt-6 border-t border-gray-300">
          <h2 className="text-xl font-semibold mb-4">Modified Document Preview</h2>
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 break-words">
              {modifiedDocument}
            </pre>
          </div>
          {/* Optional: Add buttons here for copy, save, generate PDF etc. */}
        </div>
      )}
    </div>
  );
} 