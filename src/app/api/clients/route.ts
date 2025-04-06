import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import jsPDF from 'jspdf';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
  processMarkdownForPDF,
} from '@/lib/templates';

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
      },
    });

    console.log(`Client ${newClient.id} created successfully. Proceeding to document generation.`);

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

            // Step 2b: Generate PDF
            const doc = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
            const pageMargin = 15;
            const usableWidth = doc.internal.pageSize.getWidth() - pageMargin * 2;
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(11);
            
            // Use the processed text instead of raw Markdown
            const lines = doc.splitTextToSize(processedText, usableWidth);
            let cursorY = pageMargin;
            lines.forEach((line: string) => {
              if (cursorY + 10 > doc.internal.pageSize.getHeight() - pageMargin) {
                doc.addPage();
                cursorY = pageMargin;
              }
              doc.text(line, pageMargin, cursorY);
              cursorY += 7;
            });
            
            const pdfArrayBuffer = doc.output('arraybuffer');

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


    // Return the newly created client object along with info about generated docs
    return NextResponse.json({
        ...newClient,
        generatedDocuments: generatedDocsInfo // Include info about generated docs
    }, { status: 201 }); // 201 Created

  } catch (error: any) {
    console.error('Client creation or initial document generation failed:', error);

    // Check for specific Prisma errors (like unique constraint violation) that happened during client creation
    if (error instanceof Error && (error as any).code === 'P2002' && (error as any).meta?.target?.includes('email')) {
        return NextResponse.json({ error: 'Email address already in use.' }, { status: 409 }); // 409 Conflict
    }

    // If client creation succeeded but doc gen failed partially, we might still return 201
    // but log the errors. If client creation itself failed, return 500.
    // The current logic returns 500 for any failure after validation.
    // Consider returning the client ID even if doc gen fails partially, with an error message.

    return NextResponse.json({ error: 'Internal Server Error during client creation or document generation.' }, { status: 500 });
  }
}

// 2. List All Clients (GET)
export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const clients = await prisma.client.findMany({
      orderBy: {
        onboardedAt: 'desc', // List newest clients first
      },
      // Select specific fields if needed to optimize payload size
      // select: { id: true, name: true, email: true, onboardedAt: true }
    });

    return NextResponse.json(clients);

  } catch (error) {
    console.error('Failed to fetch clients:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
} 