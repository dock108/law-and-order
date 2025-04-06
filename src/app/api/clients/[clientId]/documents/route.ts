import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase'; // Use the admin client
import { z } from 'zod';
import jsPDF from 'jspdf';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
  processMarkdownForPDF,
} from '@/lib/templates';

interface RouteParams {
  params: { clientId: string };
}

// Zod schema for the request body
const createDocumentSchema = z.object({
  documentType: z.string().min(1, { message: 'documentType is required' }), // e.g., 'demand-letter'
  // Add other potential inputs later, like uploaded content
});

const BUCKET_NAME = 'generated-documents'; // Match your Supabase bucket name

export async function POST(request: Request, { params }: RouteParams) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;
  if (!clientId) {
    return NextResponse.json({ error: 'Client ID is required' }, { status: 400 });
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = createDocumentSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }
    const { documentType } = validation.data;

    // 1. Fetch Client Data
    const client = await prisma.client.findUnique({
      where: { id: clientId },
    });
    if (!client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }

    // 2. Generate Document Content (from template)
    const templateData = prepareTemplateData(client);
    const generatedContent = await generateDocumentFromTemplate(
      documentType,
      templateData
    );

    // Process the Markdown content to remove syntax characters
    const { processedText } = processMarkdownForPDF(generatedContent);

    // 3. Generate PDF
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

    // 4. Upload PDF to Supabase Storage
    // Generate a unique filename (e.g., using client ID, doc type, timestamp)
    const timestamp = Date.now();
    const sanitizedDocType = documentType.replace(/[^a-z0-9\-\_]/gi, '_');
    const filePath = `client_${clientId}/${sanitizedDocType}_${timestamp}.pdf`; // Example path structure

    console.log(`Uploading to Supabase bucket '${BUCKET_NAME}' at path: ${filePath}`);

    const { data: uploadData, error: uploadError } = await supabaseAdmin.storage
      .from(BUCKET_NAME)
      .upload(filePath, pdfArrayBuffer, {
        contentType: 'application/pdf',
        upsert: false, // Don't overwrite existing file (optional)
      });

    if (uploadError) {
      console.error('Supabase Upload Error:', uploadError);
      throw new Error(`Failed to store document: ${uploadError.message}`);
    }

    if (!uploadData?.path) {
        throw new Error('Supabase did not return a file path after upload.');
    }

    console.log('Supabase Upload Success:', uploadData);

    // 5. Create Document Record in Prisma
    const newDocument = await prisma.document.create({
      data: {
        clientId: clientId,
        documentType: documentType, // Store the type (e.g., "demand-letter")
        fileUrl: uploadData.path, // Store the Supabase path (NOT a public URL)
        // createdAt and updatedAt handled by Prisma schema
      },
    });

    // 6. Return Success Response
    // We return the DB record, including the path. The frontend/client
    // will need to request a signed URL to actually access the file.
    return NextResponse.json(newDocument, { status: 201 });

  } catch (error: any) {
    console.error('Failed to create and store document:', error);
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// --- Add GET handler to list documents for a client ---
export async function GET(request: Request, { params }: RouteParams) {
    const session = await getServerSession(authOptions);
    if (!session) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { clientId } = params;
    if (!clientId) {
        return NextResponse.json({ error: 'Client ID is required' }, { status: 400 });
    }

    try {
        const documents = await prisma.document.findMany({
            where: {
                clientId: clientId,
            },
            orderBy: {
                createdAt: 'desc',
            },
        });

        // Here, we are just returning the document records with the path.
        // To provide download links, we need to generate signed URLs.
        // This could be done here, or preferably in a separate endpoint
        // that takes the document ID or path and returns the signed URL.
        return NextResponse.json(documents);

    } catch (error: any) {
        console.error(`Failed to fetch documents for client ${clientId}:`, error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
} 