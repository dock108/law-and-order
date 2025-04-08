import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs/promises';
import path from 'path';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
  processMarkdownForPDF,
} from '@/lib/templates';
import { generateTasksForClient } from '@/lib/tasks';

// Zod schema for validating the request body for client creation
const clientSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional().nullable(),
  incidentDate: z.string().optional().nullable().transform((val) => val ? new Date(val) : null), // Parse date string
  location: z.string().optional().nullable(),
  injuryDetails: z.string().optional().nullable(),
  medicalExpenses: z.number().optional().nullable(),
  insuranceCompany: z.string().optional().nullable(),
  lawyerNotes: z.string().optional().nullable(),
  caseType: z.string().min(1, { message: 'Case Type is required' }),
  verbalQuality: z.string().min(1, { message: 'Verbal Quality is required' }),
});

// Added Constants
const DEFAULT_ONBOARDING_TEMPLATES = ['demand-letter', 'representation-letter']; // Add more as needed
const BUCKET_NAME = 'generated-documents'; // Match Supabase bucket name

// 1. Client Creation (POST)
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let newClient; // Define client variable in outer scope

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = clientSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json({ error: 'Invalid input', details: validation.error.flatten().fieldErrors }, { status: 400 });
    }

    const clientData = validation.data;

    // Step 1: Use Prisma to create the client
    newClient = await prisma.client.create({
      data: {
        name: clientData.name,
        email: clientData.email,
        phone: clientData.phone,
        incidentDate: clientData.incidentDate,
        location: clientData.location,
        injuryDetails: clientData.injuryDetails,
        medicalExpenses: clientData.medicalExpenses,
        insuranceCompany: clientData.insuranceCompany,
        lawyerNotes: clientData.lawyerNotes,
        caseType: clientData.caseType,
        verbalQuality: clientData.verbalQuality,
      },
    });

    console.log(`Client ${newClient.id} created successfully. Proceeding to document and task generation.`);

    // START: Auto-generate default documents
    const generatedDocsInfo = [];
    for (const templateName of DEFAULT_ONBOARDING_TEMPLATES) {
        try {
            console.log(`Generating ${templateName} for client ${newClient.id}...`);

            // Step 2a: Generate Content
            const templateData = prepareTemplateData(newClient); // Use the newly created client data
            const generatedContent = await generateDocumentFromTemplate(templateName, templateData);

            // Process Markdown to remove syntax characters
            const { processedText } = processMarkdownForPDF(generatedContent);

            // Step 2b: Load Letterhead and Generate PDF
            const letterheadPath = path.resolve('./src/assets/v1_Colacci-Letterhead.pdf');
            const letterheadBytes = await fs.readFile(letterheadPath);
            const pdfDoc = await PDFDocument.load(letterheadBytes);
            const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
            const pages = pdfDoc.getPages();
            const firstPage = pages[0];
            const { width, height } = firstPage.getSize();
            const marginTop = 100, marginBottom = 50, marginLeft = 72, marginRight = 72;
            const fontSize = 11, lineHeight = 15;
            const usableWidth = width - marginLeft - marginRight;

            // Basic text splitting (same as in the other route)
            const approxCharsPerLine = Math.floor(usableWidth / (fontSize * 0.6)); 
            const words = processedText.split(/\s+/);
            const lines: string[] = [];
            let currentLine = '';
            for (const word of words) {
                const testLine = currentLine ? `${currentLine} ${word}` : word;
                if (testLine.length < approxCharsPerLine || currentLine === '') {
                    currentLine = testLine;
                } else {
                    lines.push(currentLine);
                    currentLine = word;
                }
            }
            if (currentLine) lines.push(currentLine);

            // Draw text
            let cursorY = height - marginTop;
            let currentPageIndex = 0;
            let currentPage = pages[currentPageIndex];
            for (const line of lines) {
                if (cursorY < marginBottom) {
                    currentPageIndex++;
                    if (currentPageIndex < pages.length) {
                        currentPage = pages[currentPageIndex];
                        cursorY = currentPage.getSize().height - marginTop;
                    } else {
                        currentPage = pdfDoc.addPage([width, height]);
                        cursorY = height - marginTop;
                        pages.push(currentPage);
                    }
                }
                currentPage.drawText(line, { x: marginLeft, y: cursorY, font: helveticaFont, size: fontSize, color: rgb(0, 0, 0) });
                cursorY -= lineHeight;
            }
            
            const pdfBytes = await pdfDoc.save();
            const pdfArrayBuffer = pdfBytes.buffer;

            // Step 2c: Upload to Supabase
            const timestamp = Date.now();
            const sanitizedDocType = templateName.replace(/[^a-z0-9\-_]/gi, '_');
            const filePath = `client_${newClient.id}/${sanitizedDocType}_${timestamp}.pdf`;

            const { data: uploadData, error: uploadError } = await supabaseAdmin.storage
              .from(BUCKET_NAME)
              .upload(filePath, pdfArrayBuffer, { contentType: 'application/pdf', upsert: false });

            if (uploadError) throw uploadError; // Throw error to be caught below
            if (!uploadData?.path) throw new Error('Supabase upload failed: No path returned.');

            // Step 2d: Create Document record in Prisma
            const dbDoc = await prisma.document.create({
              data: {
                clientId: newClient.id,
                documentType: templateName,
                fileUrl: uploadData.path,
              },
            });
            console.log(`Successfully generated and stored ${templateName} (ID: ${dbDoc.id})`);
            generatedDocsInfo.push({ documentType: templateName, documentId: dbDoc.id });

        } catch (docError: any) {
            // Log error for this specific document but continue to next template
            console.error(`Failed to generate/store document type "${templateName}" for client ${newClient?.id}:`, docError.message || docError);
            // Optionally, collect errors to return later if needed
        }
    }
    // END: Auto-generate default documents

    // START: Auto-generate default tasks
    let generatedTasksInfo = { count: 0, error: null };
    try {
      // Pass relevant client data to the task generator
      // This assumes clientData might have fields like caseType, verbalQuality needed by generateTasksForClient
      // You might need to adjust clientData shape or add fields to Prisma model first
      const clientInputDataForTasks = {
          caseType: (clientData as any).caseType, // Example: Assuming these fields exist or will be added
          verbalQuality: (clientData as any).verbalQuality
          // Pass other relevant fields from clientData
      };
      
      const tasksToCreate = await generateTasksForClient(newClient.id, clientInputDataForTasks);
      
      if (tasksToCreate.length > 0) {
          const result = await prisma.task.createMany({
              data: tasksToCreate,
              skipDuplicates: true, // Optional: might prevent errors if run twice, but check if needed
          });
          console.log(`Successfully generated ${result.count} tasks for client ${newClient.id}.`);
          generatedTasksInfo.count = result.count;
      } else {
          console.log(`No tasks generated for client ${newClient.id} based on selected template or template content.`);
      }
    } catch (taskError: any) {
      console.error(`Failed to generate tasks for client ${newClient.id}:`, taskError);
      generatedTasksInfo.error = taskError.message || 'Task generation failed';
      // Decide if this error should cause the whole request to fail
    }
    // END: Auto-generate default tasks

    // Return the newly created client object along with info about generated docs and tasks
    return NextResponse.json({
        ...newClient,
        generatedDocuments: generatedDocsInfo,
        generatedTasks: generatedTasksInfo, // Include info about generated tasks
    }, { status: 201 }); // 201 Created

  } catch (error: any) {
    console.error('Client creation or subsequent generation failed:', error.message, error.stack);

    // Check for specific Prisma errors (like unique constraint violation) during client creation
    if (error instanceof Error && (error as any).code === 'P2002' && (error as any).meta?.target?.includes('email')) {
      return NextResponse.json({ error: 'Email address already in use.' }, { status: 409 }); // 409 Conflict
    }

    // Determine if the error happened *after* client creation
    let specificErrorMessage = 'Internal Server Error during client processing.';
    if (error.message.includes('generateDocumentFromTemplate') || error.message.includes('processMarkdownForPDF') || error.message.includes('PDFDocument.load') || error.message.includes('fs.readFile')) {
        specificErrorMessage = 'Failed during document generation.';
    } else if (error.message.includes('supabaseAdmin.storage') || error.message.includes('upload failed')) {
        specificErrorMessage = 'Failed to upload document to storage.';
    } else if (error.message.includes('prisma.document.create')) {
        specificErrorMessage = 'Failed to save document record to database.';
    } else if (error.message.includes('generateTasksForClient') || error.message.includes('prisma.task.createMany')) {
        specificErrorMessage = 'Failed during task generation or saving.';
    }

    // If client was created but subsequent steps failed, maybe return 207 Multi-Status or similar?
    // For now, returning 500 but with a more specific message.
    return NextResponse.json({ 
        error: specificErrorMessage,
        details: error.message // Include the original error message for debugging
    }, { status: 500 });
  }
}

// 2. List All Clients (GET)
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check for query parameter to include tasks
  const { searchParams } = new URL(request.url);
  const includeTasks = searchParams.get('includeTasks') === 'true';

  try {
    const findOptions: Parameters<typeof prisma.client.findMany>[0] = {
        orderBy: {
          onboardedAt: 'desc',
        },
    };

    // If includeTasks is true, modify the options to include tasks
    if (includeTasks) {
        findOptions.include = {
            tasks: {
                orderBy: {
                    // Order tasks, e.g., by due date (nulls last), then creation date
                    dueDate: 'asc', 
                },
                // Optionally limit the number of tasks returned per client for dashboard performance
                // take: 10, 
            },
        };
        console.log("Fetching clients with included tasks...");
    } else {
        console.log("Fetching clients without tasks...");
    }

    const clients = await prisma.client.findMany(findOptions);

    // Manually process the clients array to ensure Dates are strings
    // This is crucial for proper serialization across boundaries
    const serializableClients = clients.map(client => ({
      ...client,
      // Ensure Date objects are converted to ISO strings
      onboardedAt: client.onboardedAt.toISOString(),
      updatedAt: client.updatedAt.toISOString(), 
      // If medicalExpenses (Decimal) was fetched, convert it:
      // medicalExpenses: client.medicalExpenses?.toString(),
      
      // Process tasks if they were included
      tasks: includeTasks && client.tasks ? client.tasks.map(task => ({
          ...task,
          // Ensure Date objects in tasks are converted to ISO strings
          dueDate: task.dueDate?.toISOString() || null,
          createdAt: task.createdAt.toISOString(),
          updatedAt: task.updatedAt.toISOString(),
      })) : [], // Return empty array if tasks weren't included or don't exist
    }));

    return NextResponse.json(serializableClients); // Return the processed array

  } catch (error) {
    console.error('Failed to fetch clients:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
} 