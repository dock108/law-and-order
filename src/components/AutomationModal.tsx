'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';

// Define the structure of the task data passed to the modal
interface Task {
    id: string;
    description: string;
    automationType?: string | null;
    automationConfig?: string | null;
    requiresDocs?: boolean | null;
    status: string;
}

interface AutomationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (task: Task) => void; // Pass the task data on confirm
    task: Task | null; // The task for which the automation is being triggered
    isLoading?: boolean;
    result?: any;
    error?: string | null;
    onMarkComplete: (taskId: string) => void;
}

// Helper function to generate a user-friendly description of the automation
const getAutomationDescription = (task: Task | null): string => {
    if (!task || !task.automationType) return 'No automation details available.';

    const type = task.automationType.replace(/_/g, ' ').toLowerCase();
    let details = '';

    switch (task.automationType) {
        case 'EMAIL_DRAFT':
            details = `This will prepare a draft email${task.automationConfig ? ` for '${task.automationConfig.replace(/_/g, ' ')}'` : ''}. You can review it before sending.`;
            break;
        case 'CHATGPT_SUGGESTION':
            details = `This will use AI to generate suggestions based on the task${task.automationConfig ? ` regarding '${task.automationConfig.replace(/_/g, ' ')}'` : ''}.`;
            break;
        case 'DOC_GENERATION':
            details = `This will generate the standard document${task.automationConfig ? ` template '${task.automationConfig}'` : ''} using the client's information.`;
            break;
        default:
            details = `This will trigger the '${type}' automation.`;
    }

    if (task.requiresDocs) {
        details += ' It may require specific documents to be available.';
    }

    return details;
};

const AutomationModal: React.FC<AutomationModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    task,
    isLoading = false,
    result = null,
    error = null,
    onMarkComplete,
}) => {
    if (!isOpen || !task) return null;

    const automationDescription = getAutomationDescription(task);

    const handleConfirm = () => {
        if (!isLoading && task) {
            onConfirm(task);
        }
    };

    const handleMarkTaskComplete = () => {
        if (task && !isLoading) {
            onMarkComplete(task.id);
            onClose();
        }
    };

    // Join suggestions array into a single markdown string if needed
    const suggestionsMarkdown = Array.isArray(result?.suggestions) 
        ? result.suggestions.join('\n') 
        : typeof result?.suggestions === 'string' ? result.suggestions : null;

    return (
        // Increased backdrop blur and opacity
        <div className="fixed inset-0 bg-black/50 backdrop-blur-md z-40 flex justify-center items-center p-4 transition-opacity duration-300">
            {/* Kept max-w-lg, seems reasonable, can adjust if needed */}
            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg z-50 overflow-hidden flex flex-col"> 
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
                    <h3 className="text-lg font-medium leading-6 text-gray-900">
                        {result ? 'Automation Result' : error ? 'Automation Error' : 'Confirm Automation Action'}
                    </h3>
                    {/* Add a close button to the header */} 
                    <button 
                        onClick={onClose} 
                        disabled={isLoading}
                        className={`text-gray-400 hover:text-gray-600 transition duration-150 ${isLoading ? 'cursor-not-allowed' : ''}`}
                        aria-label="Close"
                    >
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Scrollable Body */}
                <div className="p-4 max-h-[60vh] overflow-y-auto flex-grow"> 
                    {/* Loading Spinner */} 
                    {isLoading && (
                        <div className="flex flex-col justify-center items-center py-4 space-y-2">
                            <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span className="text-sm text-gray-600">Processing automation...</span>
                            {/* Add AI Patience message here */} 
                             {(task?.automationType === 'CHATGPT_SUGGESTION' || task?.automationType === 'INITIAL_CONSULT') && (
                                 <p className="text-xs text-yellow-700 mt-1">
                                     AI processing may take up to 60 seconds. Please be patient.
                                 </p>
                             )}
                        </div>
                    )}

                    {/* Error Message */} 
                    {!isLoading && error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
                            <p><strong>Error:</strong> {error}</p>
                        </div>
                    )}

                    {/* Success/Result Message */} 
                    {!isLoading && result && !error && (
                        <div className="space-y-3"> {/* Slightly reduced spacing */} 
                            <p className="text-sm font-medium text-green-800 bg-green-50 border border-green-200 px-3 py-2 rounded-md">
                                {result.message || 'Automation completed successfully.'}
                            </p>

                            {/* Render Email Draft with simulated HTML Letterhead */} 
                            {result.draft && (
                                <div>
                                    <p className="text-xs font-semibold mb-1 text-gray-600">Draft Email Preview:</p>
                                    {/* Simulated Letterhead Container */}
                                    <div className="border border-gray-300 rounded bg-white shadow-sm mt-1">
                                        {/* Simulated Header */}
                                        <div className="px-4 py-2 bg-white border-b border-gray-200">
                                            {/* Use the actual letterhead image */}
                                            <img src="/letterhead.png" alt="Law Firm Letterhead" className="w-full h-auto" />
                                            {/* Remove placeholder text */}
                                        </div>
                                        
                                        {/* Email Content Area */} 
                                        <div className={`p-4 text-sm ${typeof result.draft.body === 'string' && result.draft.body.match(/[\*\#\`\[]/) ? 'prose prose-sm max-w-none prose-headings:mt-2 prose-headings:mb-1' : ''}`}> 
                                            <p className="mb-2"><strong>To:</strong> {result.draft.to}</p>
                                            <p className="mb-3"><strong>Subject:</strong> {result.draft.subject}</p>
                                            
                                            {typeof result.draft.body === 'string' && result.draft.body.match(/[\*\#\`\[]/) ? (
                                                <ReactMarkdown>{result.draft.body}</ReactMarkdown>
                                            ) : (
                                                <pre className="whitespace-pre-wrap text-gray-700 font-sans text-sm overflow-x-auto">{result.draft.body}</pre>
                                            )}
                                        </div>

                                        {/* Simulated Footer */}
                                        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-center text-xs text-gray-500">
                                            Confidentiality Notice: This email may contain privileged information.
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Render Generated Document Info */} 
                            {result.documentInfo && (
                                <div className="mt-4">
                                    <p className="text-xs font-semibold mb-1 text-gray-600">Generated Document Preview:</p>
                                    {/* Display the generated markdown content within the letterhead simulation */} 
                                    {result.generatedMarkdown && (
                                        <div className="border border-gray-300 rounded bg-white shadow-sm mt-1">
                                            {/* Simulated Header */} 
                                            <div className="px-4 py-2 bg-white border-b border-gray-200">
                                                <img src="/letterhead.png" alt="Law Firm Letterhead" className="w-full h-auto" />
                                            </div>
                                            {/* Content Area */}
                                            <div className="mt-2 p-4 border rounded bg-white prose prose-sm max-w-none">
                                                <ReactMarkdown>{result.generatedMarkdown}</ReactMarkdown>
                                            </div>
                                            {/* Simulated Footer */} 
                                            <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-center text-xs text-gray-500">
                                                Generated Document Preview
                                            </div>
                                        </div>
                                    )}
                                     {/* Removed the simple success message div as the preview serves as confirmation */}
                                </div>
                            )}

                            {/* Render AI Suggestions/Checklist */}
                            {result.suggestions && result.suggestions.length > 0 && (
                                <div className="mt-4">
                                    <p className="text-xs font-semibold mb-1 text-gray-600">Generated Suggestions/Checklist:</p>
                                    <div className="text-sm bg-gray-50 p-3 border rounded shadow-inner prose prose-sm max-w-none">
                                        <ul>
                                            {result.suggestions.map((suggestion, index) => (
                                                <li key={index}>{suggestion}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}

                            {/* Render Mailto Link Button if available */}
                            {result.mailtoLink && (
                                <div className="mt-4">
                                    <a 
                                        href={result.mailtoLink} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                                            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                                        </svg>
                                        Open Mailto Link
                                    </a>
                                </div>
                            )}

                            {/* --- Add "Mark Complete" Button --- */}
                            {/* Show only if the task isn't already Completed */} 
                            {task?.status !== 'Completed' && (
                                <div className="pt-3 mt-3 border-t border-gray-200 text-center">
                                    <button 
                                        onClick={handleMarkTaskComplete}
                                        className="text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 px-3 py-1 transition duration-150 shadow-sm hover:shadow-md"
                                    >
                                        Mark Task Complete?
                                    </button>
                                </div>
                            )}
                            {/* --- End Button --- */}
                        </div>
                    )}

                    {/* Show Initial Confirmation Text */} 
                    {!isLoading && !result && !error && (
                        <>
                            <p className="text-sm text-gray-700 mb-2">
                                <strong>Task:</strong> {task.description}
                            </p>
                            <p className="text-sm text-gray-600 mb-4">
                                <strong>Action:</strong> {automationDescription}
                            </p>
                            
                            {/* AI Warnings (Only confidentiality warning remains here) */} 
                            {(task.automationType === 'CHATGPT_SUGGESTION' || task.automationType === 'INITIAL_CONSULT') && (
                                <div className="my-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md text-xs text-yellow-800 space-y-1">
                                    <p>
                                        <strong>Warning:</strong> This action uses an AI service (OpenAI). Avoid sending highly sensitive or privileged information.
                                    </p>
                                </div>
                            )}
                            {/* --- End AI Warnings --- */}
                            
                            <p className="text-xs text-gray-500">
                                Are you sure you want to proceed?
                            </p>
                        </>
                    )}
                </div>

                {/* Footer Buttons */} 
                <div className="bg-gray-100 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse border-t border-gray-200 flex-shrink-0">
                    {/* Show 'Begin' only before API call starts */} 
                    {!isLoading && !result && !error && (
                        <button
                            type="button"
                            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm transition duration-150"
                            onClick={handleConfirm}
                            disabled={isLoading}
                        >
                            Begin
                        </button>
                    )}
                     {/* Show 'Close' always, but disable while loading */} 
                    <button
                        type="button"
                        className={`mt-3 w-full inline-flex justify-center rounded-md border shadow-sm px-4 py-2 text-base font-medium sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition duration-150 ${isLoading ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-300'}`}
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        {result || error ? 'Close' : 'Cancel'} 
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AutomationModal; 