import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { z } from 'zod';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
} from '@/lib/templates';
import { generateTasksForClient } from '@/lib/tasks';
import { generateAndStoreInitialDocuments } from '@/lib/templates';
import { Task, Prisma } from '@prisma/client';

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

// 1. Client Creation (POST)
export async function POST(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let newClient: Prisma.ClientGetPayload<{}> | null = null; // Type Prisma client

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = clientSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json({ error: 'Invalid input', details: validation.error.flatten().fieldErrors }, { status: 400 });
    }

    // Use validated data directly (with correct types)
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

    console.log(`Client ${newClient.id} created successfully. Proceeding to task and document generation.`);

    // --- START: Generate Tasks (using refactored function) ---
    let generatedTasksInfo: any = { count: 0 }; // Initialize task info object
    try {
      // Pass the necessary fields from the *validated* and *created* client data
      const tasksToCreate = await generateTasksForClient(newClient.id, { 
          caseType: newClient.caseType, 
          verbalQuality: newClient.verbalQuality 
      });
      
      if (tasksToCreate.length > 0) {
          const result = await prisma.task.createMany({
              data: tasksToCreate,
              skipDuplicates: true,
          });
          console.log(`Successfully created ${result.count} tasks for client ${newClient.id}.`);
          generatedTasksInfo = { count: result.count };
      } else {
          console.log(`No tasks generated for client ${newClient.id}.`);
      }
    } catch (taskError: unknown) {
      console.error(`Failed to generate tasks for client ${newClient.id}:`, taskError);
      generatedTasksInfo = { error: taskError instanceof Error ? taskError.message : 'Task generation failed' };
      // Consider if this error should halt the process or just be logged
    }
    // --- END: Generate Tasks ---

    // --- START: Generate Initial Documents (using new function) ---
    let generatedDocsInfo: any[] = []; // Initialize doc info array
    try {
        // Pass the newly created client object (which includes id, caseType, etc.)
        generatedDocsInfo = await generateAndStoreInitialDocuments(newClient);
        console.log(`Document generation process completed for client ${newClient.id}. Successful: ${generatedDocsInfo.length}`);
    } catch (docError: unknown) {
        // This catch block might be redundant if generateAndStoreInitialDocuments handles internal errors,
        // but good for catching unexpected failures in the function call itself.
        console.error(`Error during initial document generation process for client ${newClient.id}:`, docError);
        // Add error info if needed for the response
        generatedDocsInfo = [{ error: "Document generation process failed." }];
    }
    // --- END: Generate Initial Documents ---

    // Return the newly created client object along with info about generated docs and tasks
    return NextResponse.json({
        ...newClient,
        generatedDocuments: generatedDocsInfo, // Include info about generated documents
        generatedTasks: generatedTasksInfo, // Include info about generated tasks
    }, { status: 201 }); // 201 Created

  } catch (error: unknown) {
    console.error('Client creation or subsequent generation failed:', error);
    const message = error instanceof Error ? error.message : "An unknown error occurred";

    // Check for specific Prisma errors (like unique constraint violation) during client creation
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
      // More specific check for email constraint
      if (error.meta?.target && (error.meta.target as string[]).includes('email')) { 
          return NextResponse.json({ error: 'Email address already in use.' }, { status: 409 }); // 409 Conflict
      }
      return NextResponse.json({ error: 'Unique constraint violation.', details: error.meta?.target }, { status: 409 });
    }

    // Determine if the error happened *after* client creation
    let specificErrorMessage = 'Internal Server Error during client processing.';
    // Update error messages to be more generic as the exact source might be within helpers
    if (message.includes('generateAndStoreInitialDocuments') || message.includes('generateAndStorePdf')) {
        specificErrorMessage = 'Failed during document generation/storage.';
    } else if (message.includes('generateTasksForClient') || message.includes('prisma.task.createMany')) {
        specificErrorMessage = 'Failed during task generation or saving.';
    }

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