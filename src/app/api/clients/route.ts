import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { z } from 'zod';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
} from '@/lib/templates';
import { generateTasksForClient } from '@/lib/tasks';
import { generateAndStorePdf } from '@/lib/documents';
import { Task } from '@prisma/client'; // Removed PrismaClient import

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

// 1. Client Creation (POST)
export async function POST(request: NextRequest) {
  const session = await getServerSession();
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

    const clientData: Record<string, unknown> = validation.data;

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

            // Call the refactored function
            const result = await generateAndStorePdf({
                markdownContent: generatedContent,
                clientId: newClient.id,
                documentType: templateName,
            });

            generatedDocsInfo.push({ documentType: templateName, documentId: result.documentId, filePath: result.filePath });

        } catch (docError: unknown) {
            // Log error for this specific document but continue to next template
            console.error(`Failed to generate/store document type "${templateName}" for client ${newClient?.id}:`, docError instanceof Error ? docError.message : docError);
            // Optionally, collect errors to return later if needed
        }
    }
    // END: Auto-generate default documents

    // START: Auto-generate default tasks
    const generatedTasksInfo: { description: string; automationType: Task['automationType']; dueDate?: Date }[] = [];
    try {
      // Pass relevant client data to the task generator
      // This assumes clientData might have fields like caseType, verbalQuality needed by generateTasksForClient
      // You might need to adjust clientData shape or add fields to Prisma model first
      const clientInputDataForTasks = {
          caseType: clientData.caseType, 
          verbalQuality: clientData.verbalQuality
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
    } catch (taskError: unknown) {
      console.error(`Failed to generate tasks for client ${newClient.id}:`, taskError);
      generatedTasksInfo.error = taskError instanceof Error ? taskError.message : 'Task generation failed';
      // Decide if this error should cause the whole request to fail
    }
    // END: Auto-generate default tasks

    // Return the newly created client object along with info about generated docs and tasks
    return NextResponse.json({
        ...newClient,
        generatedDocuments: generatedDocsInfo,
        generatedTasks: generatedTasksInfo, // Include info about generated tasks
    }, { status: 201 }); // 201 Created

  } catch (error: unknown) {
    console.error('Client creation or subsequent generation failed:', error);
    const message = error instanceof Error ? error.message : "An unknown error occurred";

    // Check for specific Prisma errors (like unique constraint violation) during client creation
    if (error instanceof Error && 'code' in error && error.code === 'P2002' && error.meta?.target?.includes('email')) {
      return NextResponse.json({ error: 'Email address already in use.' }, { status: 409 }); // 409 Conflict
    }

    // Determine if the error happened *after* client creation
    let specificErrorMessage = 'Internal Server Error during client processing.';
    if (message.includes('generateDocumentFromTemplate') || message.includes('generateAndStorePdf')) {
        specificErrorMessage = 'Failed during document generation/storage.';
    } else if (message.includes('generateTasksForClient') || message.includes('prisma.task.createMany')) {
        specificErrorMessage = 'Failed during task generation or saving.';
    }

    // If client was created but subsequent steps failed, maybe return 207 Multi-Status or similar?
    // For now, returning 500 but with a more specific message.
    return NextResponse.json({ 
        error: specificErrorMessage,
        details: message // Include the original error message for debugging
    }, { status: 500 });
  }
}

// 2. List All Clients (GET)
export async function GET(request: NextRequest) {
  const session = await getServerSession();
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
                select: {
                    id: true,
                    description: true,
                    dueDate: true,
                    status: true,
                    createdAt: true,
                    updatedAt: true,
                    notes: true,
                    clientId: true,
                    automationType: true,
                    automationConfig: true,
                    requiresDocs: true,
                },
                orderBy: [
                    { dueDate: { sort: 'asc', nulls: 'last' } },
                    { createdAt: 'asc' }
                ],
            },
        };
        console.log("Fetching clients with included tasks (including automation fields)...");
    } else {
        console.log("Fetching clients without tasks...");
    }

    const clients = await prisma.client.findMany(findOptions);

    // Manually process the clients array to ensure Dates are strings
    // The processing of tasks needs to be adjusted if using `select`
    const serializableClients = clients.map(client => ({
        ...client,
        onboardedAt: client.onboardedAt.toISOString(),
        incidentDate: client.incidentDate?.toISOString() ?? null,
        // Explicitly handle other potentially non-serializable fields
        tasks: client.tasks?.map(task => ({
             ...task,
             createdAt: task.createdAt.toISOString(),
             updatedAt: task.updatedAt.toISOString(),
             dueDate: task.dueDate?.toISOString() ?? null,
        })) ?? [], 
    }));

    return NextResponse.json(serializableClients); // Return the processed array

  } catch (error: unknown) {
    console.error('Failed to fetch clients:', error);
    const message = error instanceof Error ? error.message : "An unknown error occurred";
    return NextResponse.json({ error: `Failed to fetch clients: ${message}` }, { status: 500 });
  }
} 