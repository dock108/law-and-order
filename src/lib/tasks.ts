import fs from 'fs/promises';
import path from 'path';
import { Prisma } from '@prisma/client'; // Import Prisma types

// Define Task structure for creation - Updated for direct date parsing
interface TaskTemplateItem {
  description: string;
  dueDate: Date | null; // Store parsed date directly
}

interface ClientData {
    // Using the actual fields from the updated Client model
    caseType: string; 
    verbalQuality: string; 
    // Add other relevant fields as needed
}

/**
 * Selects the appropriate task template filename based on client data.
 */
function selectTaskTemplate(clientData: ClientData): string {
  // Point to the new template location
  const basePath = './docs/task-templates/'; 
  let filename = 'tasks-generic.md'; // Default filename

  const { caseType, verbalQuality } = clientData;

  // Refined selection logic based on caseType and verbalQuality
  if (caseType === 'MVA') {
    if (verbalQuality === 'Good') {
      filename = 'tasks-initial-mva-good-verbal.md';
    } else if (verbalQuality === 'Bad') {
      // Assuming we have a specific file for this now
      filename = 'tasks-initial-mva-bad-verbal.md'; 
    } else if (verbalQuality === 'Zero') {
      filename = 'tasks-initial-mva-zero.md';
    } 
    // If MVA but verbalQuality is 'N/A' or something else, it falls through to generic
  } else {
    // Handle non-MVA cases or other specific types
    if (verbalQuality === 'Good') {
      // Generic good verbal for non-MVA cases
      filename = 'tasks-initial-good-verbal.md'; 
    } 
    // Add more conditions for other case types (Fall, Product Liability, etc.) if needed
    // If no specific match, it defaults to tasks-generic.md
  }
  
  // Use path.resolve to get the absolute path, which is more reliable
  return path.resolve(basePath, filename);
}

/**
 * Parses Markdown content to extract tasks and specific due dates.
 * Expected format: "- [ ] Task description (due: YYYY-MM-DD)" or "- [ ] Task description"
 */
function parseTasksFromMarkdown(markdownContent: string): TaskTemplateItem[] {
  const tasks: TaskTemplateItem[] = [];
  const lines = markdownContent.split('\n');
  // Updated Regex to capture description and specific date YYYY-MM-DD
  // Looks for "- [ ] ", captures text until "(due:", then captures the date
  const taskRegex = /^\s*-\s*\[\s*\]\s+(.*?)(?:\s*\(due:\s*(\d{4}-\d{2}-\d{2})\))?\s*$/i;

  for (const line of lines) {
    const match = line.trim().match(taskRegex);
    if (match) {
      const description = match[1].trim();
      let dueDate: Date | null = null;
      if (match[2]) { // If date string was captured
          try {
              // Parse the YYYY-MM-DD string. Important: Date constructor handles this format correctly, 
              // but it parses it as UTC. Add time zone handling if specific local times are needed.
              const dateString = match[2];
              dueDate = new Date(dateString + 'T00:00:00'); // Add T00:00:00 to avoid timezone issues with Date constructor
              if (isNaN(dueDate.getTime())) { // Check if the date parsing was successful
                console.warn(`Invalid date format found: ${match[2]} in line: "${line}"`);
                dueDate = null;
              }
          } catch (e) {
              console.warn(`Error parsing date string ${match[2]} in line "${line}":`, e);
              dueDate = null;
          }
      }
      
      if (description) {
          tasks.push({ description, dueDate }); // Use the parsed date
      }
    }
  }
  return tasks;
}

/**
 * Generates a list of tasks based on client data and task templates.
 */
export async function generateTasksForClient(clientId: string, clientData: ClientData) {
  const templatePath = selectTaskTemplate(clientData);
  console.log(`Selected task template: ${templatePath}`);

  try {
    const markdownContent = await fs.readFile(templatePath, 'utf-8');
    const taskTemplates = parseTasksFromMarkdown(markdownContent);

    // Remove explicit type annotation and use simple object structure
    const tasksToCreate = taskTemplates.map(template => {
      return {
        clientId: clientId, // Provide clientId directly
        description: template.description,
        dueDate: template.dueDate, // Use the parsed date directly
        status: 'Pending', 
      };
    });

    return tasksToCreate;
  } catch (error: any) {
    // Log error if template file is missing or parsing fails
    if (error.code === 'ENOENT') {
         console.error(`Task template file not found: ${templatePath}. Falling back to empty array.`);
    } else {
        console.error(`Error reading or parsing task template ${templatePath}:`, error);
    }
    // Return empty array if template processing fails
    return [];
  }
} 