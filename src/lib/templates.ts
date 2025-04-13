import fs from 'fs/promises';
import path from 'path';
import Handlebars from 'handlebars';

interface ClientData { // Define or import a proper Client type
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    incidentDate?: Date | null;
    location?: string | null;
    // ... add other potential client fields used in templates
}

interface TemplateData extends Record<string, unknown> { // Changed from any to unknown
    clientName?: string;
    clientDobFormatted?: string;
    clientAddress?: string;
    firmName?: string;
    firmAddress?: string;
    firmPhone?: string;
    firmFax?: string;
    incidentDateFormatted?: string;
    currentDateFormatted?: string;
    location?: string;
    // ... other fields ...
}

/**
 * Loads and compiles a Handlebars template.
 * @param templateName - The name of the template file (e.g., 'demand-letter') without the .md extension.
 * @param data - The data object to populate the template with.
 * @returns The compiled template content as a string.
 * @throws If the template file is not found or cannot be read.
 */
export async function generateDocumentFromTemplate(
  templateName: string,
  data: TemplateData
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

  } catch (error: unknown) {
      console.error(`Error reading or compiling template ${templateName}:`, error);
    const message = error instanceof Error ? error.message : "Unknown template error";
    throw new Error(`Failed to generate document from template '${templateName}': ${message}`);
  }
}

/**
 * Processes Markdown text to remove syntax characters and prepare it for PDF rendering
 * @param markdownText The Markdown content to process
 * @returns A structured representation of the text with formatting information
 */
export function processMarkdownForPDF(markdownText: string): { 
  processedText: string
} {
  // Convert markdown to plain text by removing common markdown syntax
  let processedText = markdownText;
  
  // Replace headings (# Heading) with proper text
  processedText = processedText.replace(/^#{1,6}\s+(.+)$/gm, (match, heading) => {
    // Add some extra spacing before headings (except for the first one)
    return heading.toUpperCase();
  });
  
  // Add extra space after horizontal rules
  processedText = processedText.replace(/^---+$/gm, '\n\n');
  
  // Replace bold/italic markers
  processedText = processedText.replace(/\*\*(.+?)\*\*/g, '$1'); // Bold
  processedText = processedText.replace(/\*(.+?)\*/g, '$1');     // Italic
  processedText = processedText.replace(/__(.+?)__/g, '$1');     // Bold
  processedText = processedText.replace(/_(.+?)_/g, '$1');       // Italic
  
  // Replace bullet points
  processedText = processedText.replace(/^\s*[-*+]\s+/gm, '• ');
  
  // Replace numbered lists - keep the numbers
  processedText = processedText.replace(/^\s*(\d+)\.\s+/gm, '$1. ');
  
  // Replace blockquotes
  processedText = processedText.replace(/^>\s+(.+)$/gm, '    $1');
  
  // Replace code blocks with regular text (removing backticks)
  processedText = processedText.replace(/```[\s\S]+?```/g, (match) => {
    return match.replace(/```/g, '').trim();
  });
  
  // Replace inline code with regular text
  processedText = processedText.replace(/`(.+?)`/g, '$1');
  
  // Remove link syntax but keep text
  processedText = processedText.replace(/\[(.+?)\]\(.+?\)/g, '$1');
  
  // Handle tables
  // This is a simplified approach - in a real app you might want to format them better
  processedText = processedText.replace(/\|(.+?)\|/g, '$1');
  processedText = processedText.replace(/^[\|\-\s]+$/gm, '');
  
  // Add double spacing between paragraphs to improve readability
  processedText = processedText.replace(/\n\n/g, '\n\n');
  
  // Remove extra spaces
  processedText = processedText.replace(/[ \t]+\n/g, '\n');
  processedText = processedText.replace(/\n{3,}/g, '\n\n');
  
  return { processedText };
}

// --- Helper function for date formatting ---
function formatDate(dateInput: Date | string | null | undefined): string {
    if (!dateInput) return '[Date Not Provided]';
    try {
        const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
        // Consistent format
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }); 
    } catch {
        return '[Invalid Date]';
    }
}

// --- Helper function for currency formatting ---
function formatCurrency(valueInput: number | null | undefined): string {
    if (valueInput === null || valueInput === undefined) return '[Amount Not Provided]';
    try {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(valueInput);
    } catch {
        return '[Invalid Amount]';
    }
}

// --- Prepare data specifically for Handlebars context ---
// This function transforms raw client data into the shape needed by the template,
// including formatted fields.
export function prepareTemplateData(client: Partial<ClientData>): TemplateData {
    const firmDetails = { // Move firm details to env or config
        firmName: process.env.NEXT_PUBLIC_FIRM_NAME || "Hynes & Colacci Law Firm",
        firmAddress: process.env.NEXT_PUBLIC_FIRM_ADDRESS || "123 Law St, Anytown, USA",
        firmPhone: process.env.NEXT_PUBLIC_FIRM_PHONE || "555-1234",
        firmFax: process.env.NEXT_PUBLIC_FIRM_FAX || "555-5678",
    };
    
    return {
        ...client, // Spread client data (be mindful of overwrites)
        ...firmDetails,
        clientName: client.name || '[Client Name Missing]',
        incidentDateFormatted: formatDate(client.incidentDate), // Use helper
        currentDateFormatted: formatDate(new Date()), // Format current date
        location: client.location || '[Location Missing]', // Handle default here
        // Add other necessary formatted fields or derived data
        // clientDobFormatted: formatDate(client.dob), // Example
        // clientAddress: client.address || '[Address Missing]',
    };
}

// Register Handlebars helpers
Handlebars.registerHelper('date', (dateInput: Date | string | null | undefined) => {
    // Use the formatDate helper internally
    return formatDate(dateInput);
});

Handlebars.registerHelper('formatCurrency', (valueInput: number | null | undefined) => {
    if (valueInput === null || valueInput === undefined) return '[Amount Not Provided]';
    try {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(valueInput);
    } catch {
        return '[Invalid Amount]';
    }
}); 