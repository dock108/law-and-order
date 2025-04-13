'use client';

import React, { useState, useRef, useEffect } from 'react';
import { AutomationModal } from './AutomationModal'; // Use named import

// Define Task interface matching the data structure from the server
interface Task {
  id: string;
  description: string;
  dueDate: string | null;
  status: string;
  createdAt: string;
  automationType?: string | null;  // e.g., EMAIL_DRAFT, CHATGPT_SUGGESTION, DOC_GENERATION
  requiresDocs?: boolean | null;
  automationConfig?: string | null; // e.g., template name, suggestion type
}

interface TaskListProps {
  initialTasks: Task[];
  clientId: string; // Needed if we add more actions later
  onTaskUpdate: (taskId: string, newStatus: Task['status']) => void;
  onTaskDelete: (taskId: string) => void;
}

// Helper functions (can be moved to a utils file if shared)
const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'numeric', day: 'numeric' });
    } catch {
      // Just return the original string if parsing fails
      return dateString;
    }
};

const getStatusStyles = (status: string): { badge: string; dropdownItem: string; } => {
    switch (status.toLowerCase()) {
        case 'completed': return { badge: 'bg-green-100 text-green-800', dropdownItem: 'text-green-700 hover:bg-green-50' };
        case 'overdue': return { badge: 'bg-red-100 text-red-800', dropdownItem: 'text-red-700 hover:bg-red-50' }; // For display only
        case 'in progress': return { badge: 'bg-yellow-100 text-yellow-800', dropdownItem: 'text-yellow-700 hover:bg-yellow-50' };
        default: return { badge: 'bg-gray-100 text-gray-800', dropdownItem: 'text-gray-700 hover:bg-gray-50' }; // Pending
    }
};

const isTaskOverdue = (dueDateString: string | null, status: string): boolean => {
    if (!dueDateString || status.toLowerCase() === 'completed') return false;
    try {
        const dueDate = new Date(dueDateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return dueDate < today;
    } catch {
      // Return false if date parsing fails
      return false;
    }
};

// Define possible status transitions for the dropdown/buttons
const availableStatuses: Task['status'][] = ['Pending', 'In Progress', 'Completed'];

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function TaskList({ initialTasks, clientId, onTaskUpdate, onTaskDelete }: TaskListProps) {
  // We'll keep tasks state for future implementations though it's currently synced with props
  const [tasks] = useState<Task[]>(initialTasks);
  const [loadingTaskId, setLoadingTaskId] = useState<string | null>(null);
  const [openDropdownTaskId, setOpenDropdownTaskId] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // --- State for Automation Modal ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [automationResult, setAutomationResult] = useState<unknown>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [automationError, setAutomationError] = useState<string | null>(null);
  const [isAutomating, setIsAutomating] = useState(false);
  // --- End State for Automation Modal ---

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdownTaskId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [dropdownRef]);

  const handleStatusChange = async (taskId: string, newStatus: Task['status']) => {
    setLoadingTaskId(taskId);
    setOpenDropdownTaskId(null); // Close dropdown on selection
    try {
      await onTaskUpdate(taskId, newStatus);
    } catch (error: unknown) {
      console.error('Error calling task update API:', error);
      // TODO: Add user-facing error feedback
    } finally {
        setLoadingTaskId(null);
    }
  };

  const toggleDropdown = (taskId: string) => {
    setOpenDropdownTaskId(openDropdownTaskId === taskId ? null : taskId);
  };

  // --- Updated handler to open the modal ---
  const handleOpenAutomationModal = (task: Task) => {
      // Clear previous results/errors when opening modal
      setAutomationResult(null);
      setAutomationError(null);
      setSelectedTask(task);
      setIsModalOpen(true);
  };

  // --- Updated function to call the API --- 
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleAutomationStart = async (task: Task) => {
      if (!task || !task.automationType) return;

      console.log(`Starting automation API call for task ${task.id}:`, task);
      setIsAutomating(true);
      setAutomationResult(null); // Clear previous results
      setAutomationError(null); // Clear previous errors

      try {
          const response = await fetch('/api/automation', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  taskId: task.id,
                  clientId: clientId, // Pass clientId from props
                  automationType: task.automationType,
                  automationConfig: task.automationConfig,
                  requiresDocs: task.requiresDocs,
              }),
          });

          const result = await response.json();

          if (!response.ok) {
              console.error('Automation API call failed:', result);
              throw new Error(result.error || 'Failed to trigger automation');
          }

          console.log('Automation API call successful:', result);
          setAutomationResult(result); // Store the successful result

      } catch (error: unknown) {
          console.error('Error calling automation API:', error);
          setAutomationError(error instanceof Error ? error.message : 'An unknown error occurred');
          // Keep modal open to show the error
      } finally {
          setIsAutomating(false);
      }
  };

  // --- Handler for Marking Task Complete via Modal ---
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleMarkComplete = (taskId: string) => {
      console.log(`Marking task ${taskId} as complete via modal button.`);
      // Reuse the existing status change handler
      handleStatusChange(taskId, 'Completed');
  };
  // --- End Handler ---

  // handleTaskClick (keep for clicking the main task area - might be useful later)
  const handleTaskClick = (task: Task) => {
    console.log(`Task clicked: "${task.description}" for client ${clientId}`);
    // Currently does nothing if automation button exists, but could navigate or expand details
    if (task.automationType) {
        // Maybe open details instead of triggering automation directly?
        // For now, do nothing if there's an automation button.
        return;
    }
    // Prevent action if status update is loading
    if (loadingTaskId === task.id) return;

    console.log('No specific action defined for clicking this non-automated task.');
  };

  // Commented out for future implementation
  // const deleteTask = async (taskId: string) => {
  //   try {
  //     await onTaskDelete(taskId);
  //   } catch (error: unknown) {
  //     console.error('Error calling task delete API:', error);
  //     // TODO: Add user-facing error feedback
  //   }
  // };

  if (!tasks || tasks.length === 0) {
    return <p className="text-sm text-gray-500 italic">No tasks found for this client.</p>;
  }

  return (
    <>
      <ul className="space-y-3">
        {tasks.map((task) => {
          const overdue = isTaskOverdue(task.dueDate, task.status);
          const displayStatus = overdue && task.status !== 'Completed' ? 'Overdue' : task.status;
          const statusStyles = getStatusStyles(displayStatus);
          const isLoading = loadingTaskId === task.id;
          const isDropdownOpen = openDropdownTaskId === task.id;

          return (
            <li 
              key={task.id} 
              className={`relative flex items-center justify-between p-3 bg-white rounded-md border border-gray-200 shadow-sm hover:shadow-md transition duration-150 ${ 
                isLoading ? 'opacity-50 cursor-wait' : ''
              } ${ 
                isDropdownOpen ? 'z-20' : 'z-10' // Higher z-index when dropdown is open
              }`}
            >
              {/* Task Details Area */}
              <div
                className="flex-1 mr-4 group"
                // Removed onClick here, click handled by button or main task area if no automation
                title={task.automationType ? `Task: ${task.description}` : `Click to action: ${task.description}`}
              >
                <p 
                  className={`text-sm font-medium text-gray-900 ${!task.automationType ? 'cursor-pointer group-hover:text-blue-600 transition duration-150' : ''}`}
                  onClick={() => !task.automationType && handleTaskClick(task)} // Only allow click if no automation button
                >
                  {task.description}
                </p>
                <p className="text-xs text-gray-600">
                  Due: {formatDate(task.dueDate)}
                  {overdue && task.status !== 'Completed' && <span className="text-red-700 font-semibold ml-2">(Overdue)</span>}
                </p>
                {/* --- Automation Action Button --- */}
                {task.automationType && (
                  <button 
                    onClick={(event) => {
                        event.stopPropagation(); // Prevent any parent onClick
                        handleOpenAutomationModal(task); // Open the modal
                    }}
                    // Added hover scale/brightness and cursor-pointer
                    className="mt-2 px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-100 rounded hover:bg-indigo-200 hover:scale-105 hover:brightness-105 transition duration-150 cursor-pointer shadow-sm hover:shadow-md"
                    title={`Trigger action: ${task.automationType.replace(/_/g, ' ').toLowerCase()}`}
                  >
                    ⚡️ Action: {task.automationType.replace(/_/g, ' ').toLowerCase()}
                  </button>
                )}
                {/* --- End Automation Button --- */}
              </div>

              {/* Status Badge & Dropdown */}
              <div className="relative" ref={isDropdownOpen ? dropdownRef : null}> 
                {/* Clickable Status Badge - Added explicit cursor-pointer and clearer hover */}
                <button
                  onClick={() => !isLoading && toggleDropdown(task.id)}
                  disabled={isLoading}
                  // Added cursor-pointer, adjusted hover effect
                  className={`px-3 py-1 inline-flex text-xs leading-4 font-semibold rounded-full transition duration-150 shadow-sm ${statusStyles.badge} ${isLoading ? 'cursor-wait' : 'cursor-pointer hover:opacity-80 hover:shadow-md'}`}
                  title="Click to change status"
                >
                  {isLoading ? (
                      <svg className="animate-spin h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                  ) : (
                    displayStatus
                  )}
                </button>

                {/* Dropdown Menu (z-50 remains useful for stacking within the li) */}
                {isDropdownOpen && (
                  <div className="origin-top-right absolute right-0 mt-2 w-36 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
                      {availableStatuses.map((statusOption) => (
                        <button
                          key={statusOption}
                          onClick={() => handleStatusChange(task.id, statusOption)}
                          className={`block w-full text-left px-4 py-2 text-sm ${getStatusStyles(statusOption).dropdownItem} ${task.status === statusOption ? 'font-bold bg-gray-50' : ''}`}
                          role="menuitem"
                          disabled={task.status === statusOption} // Disable selecting the current status
                        >
                          {statusOption}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {/* --- Render the Modal --- */}
      <AutomationModal 
        isOpen={isModalOpen}
        onClose={() => {
            if (!isAutomating) {
                setIsModalOpen(false);
            }
        }}
        automationTask={selectedTask || { id: '', description: '', status: '' }} 
      />
      {/* --- End Render Modal --- */}
    </>
  );
} 

// Add named export alongside default export
export { TaskList }; 