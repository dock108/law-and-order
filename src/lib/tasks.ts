import { Prisma } from '@prisma/client';

// Define the structure for task data expected by Prisma
// This helps ensure the function returns the correct shape.
type TaskCreateInput = Omit<Prisma.TaskCreateManyInput, 'clientId'> & { clientId?: string };

// Task template structure
interface TaskTemplate {
  description: string;
  // Optional: Set a default relative due date (e.g., days from creation)
  // dueDateOffsetDays?: number;
  // Optional: Add automation hints if needed later
  // automationType?: string;
}

// Define task templates keyed by case type and verbal quality
// Using a nested structure for clarity
const taskTemplates: Record<string, Record<string, TaskTemplate[]>> = {
  // Default tasks for ALL clients (MVP core set)
  _default: {
    _all: [
      { description: 'Initial Client Consult' },
      { description: 'Draft Initial Demand Letter' },
      { description: 'Obtain Initial Medical Records' },
    ],
  },
  // Case Type Specific Tasks
  MVA: {
    _all: [ // Tasks for all MVA cases
      { description: 'Request Police Report' },
      { description: 'Investigate Accident Scene' },
    ],
    Good: [ // Tasks specifically for MVA + Good Verbal
      { description: 'Draft Initial Demand Letter (High Estimate)' },
    ],
    Bad: [ // Tasks specifically for MVA + Bad Verbal
      { description: 'Prepare for Litigation (Lower Initial Offer Likely)' },
    ],
    Zero: [ // Tasks specifically for MVA + Zero Verbal
      { description: 'Focus on Objective Evidence (Police Report, Medicals)' },
    ],
    // 'N/A' verbal quality for MVA will only get _default and MVA._all tasks
  },
  Fall: {
    _all: [
      { description: 'Investigate Property Conditions' },
      { description: 'Identify Property Owner/Manager' },
      { description: 'Preserve Incident Evidence (Photos, Videos)' },
    ],
    // Add verbal quality specifics if needed for Fall cases
  },
  'Product Liability': {
    _all: [
      { description: 'Identify Product Manufacturer/Distributor' },
      { description: 'Research Similar Incidents/Recalls' },
      { description: 'Preserve Product Evidence' },
    ],
  },
  Other: {
    _all: [
      { description: 'Define Specific Case Strategy' },
    ],
  },
};

/**
 * Generates a list of tasks based on client data and task templates.
 */
export async function generateTasksForClient(
  clientId: string,
  clientData: { caseType: string; verbalQuality: string }
): Promise<TaskCreateInput[]> { // Correct return type
  
  const { caseType, verbalQuality } = clientData;
  let combinedTasks: TaskTemplate[] = [];

  // 1. Add default tasks
  combinedTasks = combinedTasks.concat(taskTemplates._default?._all || []);

  // 2. Add case type specific tasks (if defined)
  const caseTypeTasks = taskTemplates[caseType];
  if (caseTypeTasks) {
    combinedTasks = combinedTasks.concat(caseTypeTasks._all || []);
    // 3. Add verbal quality specific tasks for this case type (if defined)
    combinedTasks = combinedTasks.concat(caseTypeTasks[verbalQuality] || []);
  }

  // Ensure descriptions are unique to avoid potential issues if needed later
  // (Using a Map to keep the first occurrence if duplicates exist)
  const uniqueTasksMap = new Map<string, TaskTemplate>();
  combinedTasks.forEach(task => {
    if (!uniqueTasksMap.has(task.description)) {
      uniqueTasksMap.set(task.description, task);
    }
  });

  const tasksToCreate: TaskCreateInput[] = Array.from(uniqueTasksMap.values()).map(template => {
    // Calculate due date if offset is provided (optional)
    // let dueDate: Date | null = null;
    // if (template.dueDateOffsetDays) {
    //   dueDate = new Date();
    //   dueDate.setDate(dueDate.getDate() + template.dueDateOffsetDays);
    // }

    return {
      clientId: clientId,
      description: template.description,
      status: 'Pending',
      // dueDate: dueDate, // Add calculated due date here
      // automationType: template.automationType, // Add automation hint
    };
  });

  console.log(`Generated ${tasksToCreate.length} tasks for client ${clientId} based on caseType: ${caseType}, verbalQuality: ${verbalQuality}`);
  
  return tasksToCreate;
} 