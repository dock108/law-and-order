import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase';

type Params = {
  params: {
    documentId: string;
  };
};

// GET single document
export const GET = async (request: NextRequest, { params }: Params) => {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { documentId } = params;
  
  try {
    const document = await prisma.document.findUnique({
      where: { id: documentId },
    });

    if (!document) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }

    return NextResponse.json(document);
  } catch (error: unknown) {
    console.error(`Failed to fetch document ${documentId}:`, error);
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// DELETE a document
export const DELETE = async (request: NextRequest, { params }: Params) => {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { documentId } = params;
  
  try {
    // 1. Get the document to find its file path
    const document = await prisma.document.findUnique({
      where: { id: documentId },
    });

    if (!document) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }

    // 2. Delete file from Supabase if it exists
    if (document.fileUrl) {
      const { error: deleteError } = await supabaseAdmin.storage
        .from('generated-documents')
        .remove([document.fileUrl]);
      
      if (deleteError) {
        console.error('Supabase delete error:', deleteError);
        // Continue with DB deletion even if file deletion fails
      }
    }

    // 3. Delete document record from database
    await prisma.document.delete({
      where: { id: documentId },
    });

    // Return success with no content
    return new NextResponse(null, { status: 204 });
  } catch (error: unknown) {
    console.error(`Failed to delete document ${documentId}:`, error);
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
} 