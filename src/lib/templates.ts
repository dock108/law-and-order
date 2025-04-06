import fs from 'fs/promises';
import path from 'path';
import Handlebars from 'handlebars';

/**
 * Loads and compiles a Handlebars template.
 * @param templateName - The name of the template file (e.g., 'demand-letter') without the .md extension.
 * @param data - The data object to populate the template with.
 * @returns The compiled template content as a string.
 * @throws If the template file is not found or cannot be read.
 */
export async function generateDocumentFromTemplate(
  templateName: string,
  data: Record<string, any>
): Promise<string> {
  const templatesDir = path.join(process.cwd(), 'src', 'templates');
  const templatePath = path.join(templatesDir, `${templateName}.md`);

  try {
    const templateContent = await fs.readFile(templatePath, 'utf-8');

    // Compile the template
    const compiledTemplate = Handlebars.compile(templateContent);

    // Populate the template with data
    const populatedContent = compiledTemplate(data);

    return populatedContent;

  } catch (error: any) {
    if (error.code === 'ENOENT') {
      console.error(`Template not found: ${templatePath}`);
      throw new Error(`Template '${templateName}' not found.`);
    } else {
      console.error(`Error reading or compiling template ${templateName}:`, error);
      throw new Error(`Failed to generate document from template '${templateName}'.`);
    }
  }
}

// --- Helper function for date formatting ---
function formatDate(date: Date | null | undefined): string {
    if (!date) return '[Date Not Provided]';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
}

// --- Helper function for currency formatting ---
function formatCurrency(amount: number | null | undefined): string {
    if (amount === null || amount === undefined) return '[Amount Not Provided]';
    return amount.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
    });
}

// --- Prepare data specifically for Handlebars context ---
// This function transforms raw client data into the shape needed by the template,
// including formatted fields.
export function prepareTemplateData(clientData: Record<string, any>): Record<string, any> {
    return {
        ...clientData, // Include all original client data
        clientName: clientData.name, // Map 'name' to 'clientName' if needed by template
        currentDate: formatDate(new Date()),
        incidentDateFormatted: formatDate(clientData.incidentDate),
        medicalExpensesFormatted: formatCurrency(clientData.medicalExpenses),
        // Add any other necessary formatted fields or derived data
    };
} 