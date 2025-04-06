import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma'; // Although not directly used here, keep for consistency or future use
import { z } from 'zod';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
} from '@/lib/templates';

// Zod schema for validating the incoming request body
// We expect a document type and a client data object
const generateRequestSchema = z.object({
  documentType: z.string().min(1, { message: 'documentType is required' }),
  // Define the expected shape of clientData. Adjust fields as needed for your templates.
  // This mirrors the Prisma Client model for clarity, but only includes necessary fields.
  clientData: z.object({
    id: z.string(), // Important to identify the client
    name: z.string(),
    email: z.string().email(),
    phone: z.string().optional().nullable(),
    incidentDate: z.date().optional().nullable(), // Expect Date object if fetched from DB
    location: z.string().optional().nullable(),
    injuryDetails: z.string().optional().nullable(),
    medicalExpenses: z.number().optional().nullable(), // Expect number if fetched from DB
    insuranceCompany: z.string().optional().nullable(),
    // Add other fields from Client model if your templates use them
  }),
});

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const rawData = await request.json();

    // Validate the request body
    // NOTE: If incidentDate/medicalExpenses are sent as strings/numbers from client-side,
    //       you might need to adjust the schema or parse them before validation/preparation.
    //       Assuming here the data passed matches the schema (e.g., fetched server-side first).
    const validation = generateRequestSchema.safeParse(rawData);
    if (!validation.success) {
      console.error("Validation Errors:", validation.error.flatten().fieldErrors);
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    const { documentType, clientData } = validation.data;

    // Prepare the data specifically for Handlebars (formatting, etc.)
    const templateData = prepareTemplateData(clientData);

    // Generate the document content using the utility function
    const populatedContent = await generateDocumentFromTemplate(
      documentType, // e.g., 'demand-letter'
      templateData
    );

    // Return the populated content as markdown
    return new NextResponse(populatedContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
      },
    });

  } catch (error: any) {
    console.error('Document generation failed:', error);

    // Specific error handling for template not found
    if (error.message.includes('not found')) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }

    // General error
    return NextResponse.json(
      { error: error.message || 'Failed to generate document' },
      { status: 500 }
    );
  }
} 