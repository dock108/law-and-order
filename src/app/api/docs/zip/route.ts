import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase';
import { z } from 'zod';
import JSZip from 'jszip';

const BUCKET_NAME = 'generated-documents';

// Zod schema for the request body: accepts either clientId OR documentIds
const zipRequestSchema = z.union([
  z.object({
    clientId: z.string().uuid(),
    documentIds: z.undefined(),
  }),
  z.object({
    clientId: z.undefined(),
    documentIds: z.array(z.string().uuid()).min(1),
  }),
]).refine(data => data.clientId || data.documentIds, {
  message: "Either clientId or documentIds must be provided",
});


export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = zipRequestSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }
    const { clientId, documentIds } = validation.data;

    let documents;
    let clientName = 'Selected'; // Default for filename if using documentIds

    // 1. Fetch Document Records from Prisma
    if (clientId) {
      const clientWithDocs = await prisma.client.findUnique({
        where: { id: clientId },
        include: {
          documents: { // Fetch related documents
            orderBy: { createdAt: 'desc' },
          },
        },
      });
      if (!clientWithDocs) {
        return NextResponse.json({ error: 'Client not found' }, { status: 404 });
      }
      documents = clientWithDocs.documents;
      clientName = clientWithDocs.name || `Client_${clientId.substring(0, 8)}`; // Use client name for filename
    } else if (documentIds) {
      documents = await prisma.document.findMany({
        where: {
          id: { in: documentIds },
          // Optional: Add a check for user ownership if implementing multi-user later
          // userId: session.user.id
        },
        orderBy: { createdAt: 'desc' },
      });
      if (documents.length === 0) {
         return NextResponse.json({ error: 'No documents found matching the provided IDs' }, { status: 404 });
      }
       if (documents.length !== documentIds.length) {
         console.warn('Not all requested document IDs were found or accessible.');
         // Decide if this should be an error or just proceed with found documents
      }
    } else {
       // This case should theoretically not be reached due to Zod validation
       return NextResponse.json({ error: 'Invalid request state' }, { status: 400 });
    }

    if (!documents || documents.length === 0) {
      return NextResponse.json({ error: 'No documents found to zip' }, { status: 404 });
    }

    // 2. Fetch PDFs from Supabase and Create ZIP
    const zip = new JSZip();
    for (const doc of documents) {
      if (!doc.fileUrl) {
        console.warn(`Document ${doc.id} has no fileUrl, skipping.`);
        continue;
      }

      try {
        const { data: blob, error: downloadError } = await supabaseAdmin.storage
          .from(BUCKET_NAME)
          .download(doc.fileUrl);

        if (downloadError) {
          console.error(`Failed to download ${doc.fileUrl}:`, downloadError);
          // Decide how to handle: skip this file, or fail the whole request?
          // For now, we'll skip and continue.
          continue;
        }

        if (blob) {
          const buffer = Buffer.from(await blob.arrayBuffer());
          // Sanitize document type for use in filename
          const safeDocType = doc.documentType.replace(/[^a-z0-9\-\_]/gi, '_');
          const filenameInZip = `${safeDocType}_${doc.id.substring(0, 8)}.pdf`;
          zip.file(filenameInZip, buffer);
        }
      } catch (err) {
         console.error(`Error processing file for document ${doc.id} (${doc.fileUrl}):`, err);
         // Skip this file on error
      }
    }

    // Check if any files were actually added to the zip
    const fileCount = Object.keys(zip.files).length;
    if (fileCount === 0) {
        return NextResponse.json({ error: 'No files could be retrieved or added to the ZIP archive.' }, { status: 500 });
    }

    // 3. Generate ZIP Buffer
    const zipBuffer = await zip.generateAsync({
        type: 'nodebuffer',
        compression: "DEFLATE",
        compressionOptions: {
            level: 6 // Balance between speed and compression
        }
     });

    // 4. Prepare Response
    // Sanitize client name for the final ZIP filename
    const safeClientName = clientName.replace(/[^a-z0-9\-\_\s]/gi, '_').replace(/\s+/g, '_');
    const zipFilename = `${safeClientName}_Documents_${new Date().toISOString().split('T')[0]}.zip`;

    return new NextResponse(zipBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': `attachment; filename="${zipFilename}"`,
      },
    });

  } catch (error: unknown) {
    console.error("Error creating zip:", error);
    const message = error instanceof Error ? error.message : "Unknown zip error";
    return NextResponse.json({ error: `Failed to create zip file: ${message}` }, { status: 500 });
  }
} 