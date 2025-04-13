import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { z } from 'zod';
import jsPDF from 'jspdf';
import * as pdfMake from 'pdfmake/build/pdfmake';
import * as pdfFonts from 'pdfmake/build/vfs_fonts';

// Assign vfs to pdfMake
(pdfMake as unknown).vfs = pdfFonts.pdfMake.vfs;

// Zod schema for validating the incoming request body
const pdfRequestSchema = z.object({
  content: z.string().min(1, { message: 'Document content cannot be empty' }),
  filename: z.string().optional().default('document.pdf'), // Optional filename
});

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = pdfRequestSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    const { content, filename: rawFilename } = validation.data;

    // Sanitize filename
    const filename = rawFilename.replace(/[^a-z0-9\.\-\_]/gi, '_') + 
                    (!rawFilename.toLowerCase().endsWith('.pdf') ? '.pdf' : '');

    // Initialize jsPDF
    const doc = new jsPDF({
      orientation: 'p', // portrait
      unit: 'mm', // millimeters
      format: 'a4', // A4 paper size
    });

    // --- Basic PDF Formatting ---
    const pageMargin = 15; // mm
    const pageHeight = doc.internal.pageSize.getHeight();
    const pageWidth = doc.internal.pageSize.getWidth();
    const usableWidth = pageWidth - pageMargin * 2;
    let cursorY = pageMargin;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);

    // Process content (split into lines that fit the page width)
    const lines = doc.splitTextToSize(content, usableWidth);

    lines.forEach((line: string) => {
      // Check if content exceeds page height
      if (cursorY + 10 > pageHeight - pageMargin) {
        // Add a new page if needed
        doc.addPage();
        cursorY = pageMargin; // Reset cursor to top margin
      }

      // Add text line to the PDF
      doc.text(line, pageMargin, cursorY);
      cursorY += 7; // Move cursor down for the next line (adjust line height as needed)
    });

    // Generate PDF output as ArrayBuffer
    const pdfOutput = doc.output('arraybuffer');

    // Return the PDF as a response
    return new NextResponse(pdfOutput, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${filename}"`, // Prompt download
      },
    });

  } catch (error: unknown) {
    console.error("Error generating or uploading PDF:", error);
    const message = error instanceof Error ? error.message : "Unknown PDF error";
    return NextResponse.json({ error: `PDF Generation Error: ${message}` }, { status: 500 });
  }
} 