import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase'; // Use the admin client
import { z } from 'zod';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib'; // Import pdf-lib components
import fs from 'fs/promises'; // Import fs/promises to read the letterhead
import path from 'path'; // Import path for resolving file paths
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
  processMarkdownForPDF,
} from '@/lib/templates';

// RouteParams interface removed

// Zod schema for the request body
const createDocumentSchema = z.object({
  documentType: z.string().min(1, { message: 'documentType is required' }), // e.g., 'demand-letter'
  // Add other potential inputs later, like uploaded content
});

const BUCKET_NAME = 'generated-documents'; // Match your Supabase bucket name

// Corrected POST handler signature (removed type annotation for { params })
export async function POST(request: NextRequest, { params }) {
  const session = await getServerSession();
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

    // 3. Load Letterhead and Prepare PDF
    const letterheadPath = path.resolve('./src/assets/v1_Colacci-Letterhead.pdf');
    const letterheadBytes = await fs.readFile(letterheadPath);
    const pdfDoc = await PDFDocument.load(letterheadBytes);
    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const pages = pdfDoc.getPages();
    const firstPage = pages[0]; // Assume we draw on the first page initially

    const { width, height } = firstPage.getSize();

    // --- Define Margins and Text Settings ---
    // Adjust these values based on the letterhead layout
    const marginTop = 100; // Increased top margin to avoid header
    const marginBottom = 50;
    const marginLeft = 72; // Approx 1 inch
    const marginRight = 72;
    const fontSize = 11;
    const lineHeight = 15; // Adjust line spacing
    const usableWidth = width - marginLeft - marginRight;

    // --- Prepare Text Lines (Basic Splitting) ---
    // pdf-lib doesn't have a built-in text wrapper like jsPDF.splitTextToSize.
    // We need a more robust way to split lines based on font metrics for production.
    // For this example, we'll use a simpler split based on characters per line (approximation).
    // A more accurate approach would measure text width with the chosen font.
    const approxCharsPerLine = Math.floor(usableWidth / (fontSize * 0.6)); // Rough estimate
    const words = processedText.split(/\\s+/);
    const lines: string[] = [];
    let currentLine = '';
    for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        // Very basic check, replace with proper text width measurement if needed
        if (testLine.length < approxCharsPerLine || currentLine === '') {
            currentLine = testLine;
        } else {
            lines.push(currentLine);
            currentLine = word;
        }
    }
    if (currentLine) {
        lines.push(currentLine); // Add the last line
    }

    // --- Draw Text onto Pages ---
    let cursorY = height - marginTop; // Start drawing from top margin
    let currentPageIndex = 0;
    let currentPage = pages[currentPageIndex];

    for (const line of lines) {
      // Check if we need to add a new page
      if (cursorY < marginBottom) {
          // Try to use subsequent pages from the letterhead template if they exist
          currentPageIndex++;
          if (currentPageIndex < pages.length) {
              currentPage = pages[currentPageIndex];
              // Reset cursor Y based on the potentially different height of the new page from template
              cursorY = currentPage.getSize().height - marginTop; 
          } else {
              // If letterhead pages run out, add a new blank page
              currentPage = pdfDoc.addPage([width, height]); // Use dimensions from the first page
              cursorY = height - marginTop; // Reset Y for the new blank page
              pages.push(currentPage); // Add to our tracked pages
          }
      }

      currentPage.drawText(line, {
        x: marginLeft,
        y: cursorY,
        font: helveticaFont,
        size: fontSize,
        color: rgb(0, 0, 0), // Black text
      });
      cursorY -= lineHeight; // Move cursor down
    }
    
    // 4. Save the Modified PDF
    const pdfBytes = await pdfDoc.save();
    const pdfArrayBuffer = pdfBytes.buffer; // Convert Uint8Array to ArrayBuffer

    // 5. Upload PDF to Supabase Storage
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

    // 6. Create Document Record in Prisma
    const newDocument = await prisma.document.create({
      data: {
        clientId: clientId,
        documentType: documentType, // Store the type (e.g., "demand-letter")
        fileUrl: uploadData.path, // Store the Supabase path (NOT a public URL)
        // createdAt and updatedAt handled by Prisma schema
      },
    });

    // 7. Return Success Response
    // We return the DB record, including the path. The frontend/client
    // will need to request a signed URL to actually access the file.
    return NextResponse.json(newDocument, { status: 201 });

  } catch (error: unknown) {
    console.error('Failed to create and store document:', error);
    const message = error instanceof Error ? error.message : 'Internal Server Error'
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// Corrected GET handler signature (removed type annotation for { params })
export async function GET(request: NextRequest, { params }) {
    const session = await getServerSession();
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

    } catch (error: unknown) {
        console.error(`Failed to fetch documents for client ${clientId}:`, error);
        const message = error instanceof Error ? error.message : 'Internal Server Error'
        return NextResponse.json({ error: message }, { status: 500 });
    }
}

// Removed PUT as it wasn't fully implemented and caused errors
/*
export async function PUT(request: NextRequest, { params }) {
    // ... implementation ...
}
*/ 