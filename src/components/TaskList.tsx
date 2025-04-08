'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // Use for potential refresh after update

// Define Task interface matching the data structure from the server
interface Task {
  id: string;
  description: string;
  dueDate: string | null;
  status: string;
  createdAt: string;
}

interface TaskListProps {
  initialTasks: Task[];
  clientId: string; // Needed if we add more actions later
}

// Helper functions (can be moved to a utils file if shared)
const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'numeric', day: 'numeric' });
    } catch (e) { return dateString; }
};

const getStatusBadge = (status: string) => {
    // Keep consistent with server component
    switch (status.toLowerCase()) {
        case 'completed': return 'bg-green-100 text-green-800';
        case 'overdue': return 'bg-red-100 text-red-800';
        case 'in progress': return 'bg-yellow-100 text-yellow-800';
        default: return 'bg-gray-100 text-gray-800';
    }
};

const isTaskOverdue = (dueDateString: string | null, status: string): boolean => {
    if (!dueDateString || status.toLowerCase() === 'completed') return false;
    try {
        const dueDate = new Date(dueDateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return dueDate < today;
    } catch (e) { return false; }
};

// Define possible status transitions for the dropdown/buttons
const taskStatuses: Task['status'][] = ['Pending', 'In Progress', 'Completed'];

export default function TaskList({ initialTasks, clientId }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [loadingTaskId, setLoadingTaskId] = useState<string | null>(null);
  const router = useRouter();

  const handleStatusChange = async (taskId: string, newStatus: Task['status']) => {
    setLoadingTaskId(taskId); // Indicate loading state for this specific task
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Failed to update task status:', errorData);
        // TODO: Show error message to user
        return; 
      }

      const updatedTask = await response.json();

      // Update the local state
      setTasks(currentTasks =>
        currentTasks.map(task =>
          task.id === taskId ? { ...task, status: updatedTask.status } : task
        )
      );
      
      // Optionally refresh server data if needed, though local state update is often sufficient for UI
      // router.refresh(); 

    } catch (error) {
      console.error('Error calling task update API:', error);
      // TODO: Show error message to user
    } finally {
        setLoadingTaskId(null); // Clear loading state
    }
  };

  if (!tasks || tasks.length === 0) {
    return <p className="text-sm text-gray-500 italic">No tasks found for this client.</p>;
  }

  return (
    <ul className="space-y-3">
      {tasks.map((task) => {
        const overdue = isTaskOverdue(task.dueDate, task.status);
        const statusClass = overdue && task.status !== 'Completed' ? getStatusBadge('overdue') : getStatusBadge(task.status);
        const isLoading = loadingTaskId === task.id;

        return (
          <li key={task.id} className={`flex items-center justify-between p-3 bg-white rounded-md border border-gray-200 shadow-sm hover:shadow-md transition duration-150 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <div className="flex-1 mr-4">
              <p className="text-sm font-medium text-gray-900">{task.description}</p>
              <p className="text-xs text-gray-600">
                Due: {formatDate(task.dueDate)}
                {overdue && task.status !== 'Completed' && <span className="text-red-700 font-semibold ml-2">(Overdue)</span>}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 inline-flex text-xs leading-4 font-semibold rounded-full ${statusClass}`}>
                {task.status}
              </span>
              
              {/* Complete button for non-completed tasks */}
              {task.status !== 'Completed' && (
                <button
                  onClick={() => handleStatusChange(task.id, 'Completed')}
                  disabled={isLoading}
                  className={`px-2 py-1 text-xs font-medium rounded ${isLoading ? 'bg-gray-300' : 'bg-green-500 hover:bg-green-600'} text-white transition duration-150 shadow-sm disabled:opacity-70`}
                >
                  {isLoading ? '...' : 'Complete'}
                </button>
              )}
              
              {/* Revert button for completed tasks */}
              {task.status === 'Completed' && (
                <button
                  onClick={() => handleStatusChange(task.id, 'In Progress')}
                  disabled={isLoading}
                  className={`px-2 py-1 text-xs font-medium rounded ${isLoading ? 'bg-gray-300' : 'bg-yellow-500 hover:bg-yellow-600'} text-white transition duration-150 shadow-sm disabled:opacity-70`}
                  title="Revert to In Progress"
                >
                  {isLoading ? '...' : 'Revert'}
                </button>
              )}
              
              {/* Alternative: Dropdown for multiple statuses */}
              {/* Consider using a dropdown component library for better UX */}
              {/* <select 
                 value={task.status}
                 disabled={isLoading}
                 onChange={(e) => handleStatusChange(task.id, e.target.value as Task['status'])}
                 className="text-xs rounded border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 disabled:opacity-70"
              >
                 {taskStatuses.map(s => <option key={s} value={s}>{s}</option>)}
              </select> */} 
            </div>
          </li>
        );
      })}
    </ul>
  );
} 