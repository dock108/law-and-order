import { supabaseAdmin } from '@/lib/supabase';
import { PrismaClient } from '@prisma/client';
import { processMarkdownForPDF } from './templates';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs/promises';
import path from 'path';
import prisma from '@/lib/prisma';

const BUCKET_NAME = 'generated-documents';
const LETTERHEAD_PATH = path.resolve('./src/assets/v1_Colacci-Letterhead.pdf');

interface GeneratePdfParams {
    markdownContent: string;
    clientId: string;
    documentType: string;
}

interface PdfGenerationResult {
    filePath: string;
    documentId: string;
}

/**
 * Generates a PDF document with letterhead, uploads it to Supabase,
 * and creates a corresponding Document record in Prisma.
 */
export async function generateAndStorePdf({
    markdownContent,
    clientId,
    documentType,
}: GeneratePdfParams): Promise<PdfGenerationResult> {
    try {
        console.log(`Generating PDF for type "${documentType}" for client ${clientId}...`);

        // 1. Process Markdown
        const { processedText } = processMarkdownForPDF(markdownContent);

        // 2. Load Letterhead and Generate PDF
        const letterheadBytes = await fs.readFile(LETTERHEAD_PATH);
        const pdfDoc = await PDFDocument.load(letterheadBytes);
        const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
        const pages = pdfDoc.getPages();
        const firstPage = pages[0];
        const { width, height } = firstPage.getSize();
        const marginTop = 100, marginBottom = 50, marginLeft = 72, marginRight = 72;
        const fontSize = 11, lineHeight = 15;
        const usableWidth = width - marginLeft - marginRight;

        // Basic text splitting
        const approxCharsPerLine = Math.floor(usableWidth / (fontSize * 0.6));
        const words = processedText.split(/\s+/); // Use standard space regex
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

        // 3. Upload to Supabase
        const timestamp = Date.now();
        const sanitizedDocType = documentType.replace(/[^a-z0-9\-_.]/gi, '_');
        const filePath = `client_${clientId}/${sanitizedDocType}_${timestamp}.pdf`;

        const { data: uploadData, error: uploadError } = await supabaseAdmin.storage
            .from(BUCKET_NAME)
            .upload(filePath, pdfBytes, {
                contentType: 'application/pdf',
                upsert: true,
            });

        if (uploadError) {
            console.error('Supabase Upload Error Details:', uploadError);
            throw new Error(`Supabase upload error: ${uploadError.message}`);
        }
        if (!uploadData?.path) {
            throw new Error('Supabase upload succeeded but no path was returned.');
        }

        // 4. Create Document record in Prisma
        const dbDoc = await prisma.document.create({
            data: {
                clientId: clientId,
                documentType: documentType,
                fileUrl: uploadData.path, // Use the actual path returned by Supabase
            },
        });
        console.log(`Successfully generated and stored PDF (DB ID: ${dbDoc.id}) at path: ${uploadData.path}`);

        return { filePath: uploadData.path, documentId: dbDoc.id };

    } catch (error: unknown) {
        console.error(`Error in generateAndStorePdf for type "${documentType}", client ${clientId}:`, error);
        throw new Error(`Failed to generate and store PDF for ${documentType}. Reason: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
} 