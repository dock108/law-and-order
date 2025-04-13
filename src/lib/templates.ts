import fs from 'fs/promises';
import path from 'path';
import Handlebars from 'handlebars';
// import { Prisma } from '@prisma/client'; // Removed unused import
import { generateAndStorePdf } from '@/lib/documents'; // Import the PDF generation function

// Define Client type more completely (mirror Prisma model where possible)
interface Client {
    id: string;
    name: string;
    email: string;
    phone?: string | null;
    incidentDate?: Date | null;
    location?: string | null;
    caseType: string; // Required for logic
    verbalQuality: string; // Required for logic
    // ... other client fields ...
}

interface TemplateData extends Record<string, unknown> {
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

// Define mapping for initial document generation
const documentTemplates: Record<string, Record<string, string[]>> = {
  _default: {
    _all: ['representation-letter'], // Always generate this
  },
  MVA: {
    _all: ['mva-intake-form', 'medical-records-request'],
    Good: ['demand-letter-high-estimate'],
    Bad: ['demand-letter-standard'],
    Zero: ['notice-of-claim'],
  },
  Fall: {
    _all: ['fall-intake-form', 'spoliation-letter', 'medical-records-request'],
  },
  'Product Liability': {
    _all: ['product-liability-intake', 'preservation-request'],
  },
  // 'Other' uses only defaults for now
};

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
    const compiledTemplate = Handlebars.compile(templateContent);
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
// Used in Handlebars helper registration below
export function formatCurrency(valueInput: number | null | undefined): string {
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
export function prepareTemplateData(client: Partial<Client>): TemplateData {
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

// --- NEW: Generate and store initial documents based on client data ---
/**
 * Determines applicable document templates, generates them using client data,
 * stores them as PDFs in Supabase, and creates Prisma Document records.
 */
export async function generateAndStoreInitialDocuments(
    client: Client // Expect a complete client object after creation
): Promise<Array<{ documentType: string; documentId: string; filePath: string }>> {
    const { id: clientId, caseType, verbalQuality } = client;
    let applicableTemplates: string[] = [];
    const generatedDocsInfo = [];

    // 1. Determine applicable templates
    applicableTemplates = applicableTemplates.concat(documentTemplates._default?._all || []);
    const caseTemplates = documentTemplates[caseType];
    if (caseTemplates) {
        applicableTemplates = applicableTemplates.concat(caseTemplates._all || []);
        applicableTemplates = applicableTemplates.concat(caseTemplates[verbalQuality] || []);
    }
    // Remove duplicates
    applicableTemplates = [...new Set(applicableTemplates)];

    console.log(`Client ${clientId}: Determined initial document templates:`, applicableTemplates);

    // 2. Generate and store each document
    for (const templateName of applicableTemplates) {
        try {
            console.log(`Generating document "${templateName}" for client ${clientId}...`);
            const templateData = prepareTemplateData(client);
            const generatedContent = await generateDocumentFromTemplate(templateName, templateData);
            
            // Call the existing PDF generation/storage function
            const result = await generateAndStorePdf({
                markdownContent: generatedContent,
                clientId: clientId,
                documentType: templateName,
            });

            generatedDocsInfo.push({ documentType: templateName, documentId: result.documentId, filePath: result.filePath });
            console.log(`Successfully generated and stored "${templateName}" for client ${clientId}. Path: ${result.filePath}`);

        } catch (docError: unknown) {
            // Log error for this specific document but continue to next template
            console.error(`Failed to generate/store document type "${templateName}" for client ${clientId}:`, docError instanceof Error ? docError.message : docError);
            // Optionally, collect errors to return later if needed
        }
    }

    return generatedDocsInfo;
}

// Register Handlebars helpers
Handlebars.registerHelper('date', (dateInput: Date | string | null | undefined) => {
    // Use the formatDate helper internally
    return formatDate(dateInput);
});

Handlebars.registerHelper('formatCurrency', (valueInput: number | null | undefined) => {
    // Use the exported formatCurrency function
    return formatCurrency(valueInput);
}); 