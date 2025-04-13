import { NextResponse, NextRequest } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase';

interface RouteParams {
  params: { documentId: string };
}

const BUCKET_NAME = 'generated-documents'; // Match your Supabase bucket name
const SIGNED_URL_EXPIRES_IN = 60 * 5; // URL valid for 5 minutes

export const GET = async (req: NextRequest, { params }: RouteParams) => {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { documentId } = params;
  if (!documentId) {
    return NextResponse.json({ error: 'Document ID is required' }, { status: 400 });
  }

  try {
    // 1. Fetch the Document record from Prisma to get the file path
    const document = await prisma.document.findUnique({
      where: { id: documentId },
    });

    if (!document) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }

    // Ensure the user is authorized to access this client's document (optional but recommended)
    // e.g., if implementing multi-user later, check if session.user.id owns client record

    const filePath = document.fileUrl; // Path stored in DB (e.g., 'client_.../....pdf')

    // 2. Generate a signed URL from Supabase
    const { data, error } = await supabaseAdmin.storage
      .from(BUCKET_NAME)
      .createSignedUrl(filePath, SIGNED_URL_EXPIRES_IN, {
          // Optional: Add download attribute to force download prompt
          // download: true // or download: 'desired_filename.pdf'
      });

    if (error) {
      console.error('Supabase Signed URL Error:', error);
      throw new Error(`Failed to create signed URL: ${error.message}`);
    }

    if (!data?.signedUrl) {
        throw new Error('Supabase did not return a signed URL.');
    }

    // 3. Return the signed URL in the response
    // The client-side can then use this URL for downloading/displaying
    // Option 1: Return JSON with the URL
    return NextResponse.json({ downloadUrl: data.signedUrl });

    // Option 2: Redirect the user directly to the signed URL
    // return NextResponse.redirect(data.signedUrl, 302);

  } catch (error: unknown) {
    console.error(`Failed to get download URL for document ${params.documentId}:`, error);
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
} 