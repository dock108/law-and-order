import fs from 'fs/promises';
import path from 'path';
import Handlebars from 'handlebars';
import { marked } from 'marked';
import { NextResponse, NextRequest } from 'next/server';

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
  
  // Replace Handlebars placeholders temporarily to protect them
  // const handlebarsPlaceholders: string[] = [];
  // processedText = processedText.replace(/{{(.+?)}}/g, (match, content) => {
  //   handlebarsPlaceholders.push(content.trim());
  //   return `[[PLACEHOLDER_${handlebarsPlaceholders.length - 1}]]`;
  // });
  
  // Add double spacing between paragraphs to improve readability
  processedText = processedText.replace(/\n\n/g, '\n\n');
  
  // Remove extra spaces
  processedText = processedText.replace(/[ \t]+\n/g, '\n');
  processedText = processedText.replace(/\n{3,}/g, '\n\n');
  
  // Restore Handlebars placeholders
  // handlebarsPlaceholders.forEach((content, index) => {
  //   processedText = processedText.replace(
  //     `[[PLACEHOLDER_${index}]]`,
  //     `{{${content}}}`
  //   );
  // });
  
  return { processedText };
}

// --- Helper function for date formatting ---
function formatDate(date: Date | string | null, format: string = 'yyyy-MM-dd'): string {
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

// Register Handlebars helpers
Handlebars.registerHelper('date', (date: Date | string | null, options: any) => {
    // ... helper body ...
});

Handlebars.registerHelper('formatCurrency', (value: number | null | undefined) => {
    // ... helper body ...
}); 