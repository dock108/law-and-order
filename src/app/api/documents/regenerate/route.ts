import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { z } from 'zod';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase';
import {
    prepareTemplateData,
    generateDocumentFromTemplate,
    processMarkdownForPDF // Import processing if needed for PDF generation
} from '@/lib/templates';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs/promises';
import path from 'path';

const BUCKET_NAME = 'generated-documents';
const LETTERHEAD_PATH = path.resolve('./src/assets/v1_Colacci-Letterhead.pdf');

// Zod schema for request validation
const regenerateSchema = z.object({
  documentId: z.string().min(1, "Document ID is required"),
  clientId: z.string().min(1, "Client ID is required"),
  documentType: z.string().min(1, "Document type/template name is required"),
});

// --- POST Handler for Regeneration ---
export async function POST(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const rawData = await request.json();
    const validation = regenerateSchema.safeParse(rawData);

    if (!validation.success) {
      return NextResponse.json({ error: 'Invalid input', details: validation.error.flatten().fieldErrors }, { status: 400 });
    }

    const { documentId, clientId, documentType } = validation.data;

    // 1. Fetch latest client data
    const client = await prisma.client.findUnique({
        where: { id: clientId },
    });
    if (!client) {
        return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }

    // 2. Fetch existing document record to get the file path
    const existingDocument = await prisma.document.findUnique({
        where: { id: documentId },
    });
    if (!existingDocument || !existingDocument.fileUrl) {
        return NextResponse.json({ error: 'Original document record or file path not found' }, { status: 404 });
    }
    const filePath = existingDocument.fileUrl; // The path to overwrite in Supabase

    console.log(`Regenerating document type "${documentType}" for client ${clientId}. Overwriting path: ${filePath}`);

    // 3. Generate new Markdown content using the latest client data
    const templateData = prepareTemplateData(client);
    const generatedContent = await generateDocumentFromTemplate(documentType, templateData);

    // 4. Generate new PDF bytes (adapted from generateAndStorePdf)
    const { processedText } = processMarkdownForPDF(generatedContent);
    const letterheadBytes = await fs.readFile(LETTERHEAD_PATH);
    const pdfDoc = await PDFDocument.load(letterheadBytes);
    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const pages = pdfDoc.getPages();
    const firstPage = pages[0];
    const { width, height } = firstPage.getSize();
    const marginTop = 100, marginBottom = 50, marginLeft = 72, marginRight = 72;
    const fontSize = 11, lineHeight = 15;
    const usableWidth = width - marginLeft - marginRight;
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

    // 5. Upload to Supabase, overwriting the existing file at the specific path
    console.log(`Uploading regenerated PDF to Supabase path: ${filePath}`);
    const { data: uploadData, error: uploadError } = await supabaseAdmin.storage
        .from(BUCKET_NAME)
        .upload(filePath, pdfBytes, {
            contentType: 'application/pdf',
            upsert: true, // IMPORTANT: Overwrite the existing file
        });

    if (uploadError) {
        console.error('Supabase Upload Error on Regeneration:', uploadError);
        throw new Error(`Failed to overwrite document in storage: ${uploadError.message}`);
    }
    if (!uploadData?.path) {
        throw new Error('Supabase did not return a path after regeneration upload.');
    }

    // 6. (Optional) Update the timestamp in Prisma
    const updatedDocument = await prisma.document.update({
        where: { id: documentId },
        data: { updatedAt: new Date() }, // Prisma automatically handles updatedAt if schema is set up
    });

    console.log(`Successfully regenerated document ${documentId} at path: ${filePath}`);

    // 7. Return success response
    return NextResponse.json({
        message: `Document '${documentType}' regenerated successfully.`,
        document: updatedDocument, // Return updated record
    });

  } catch (error: unknown) {
    console.error(`Error regenerating document:`, error);
    const message = error instanceof Error ? error.message : 'Internal Server Error during regeneration'
    return NextResponse.json({ error: message }, { status: 500 });
  }
} 