import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { Prisma } from '@prisma/client';
import { supabaseAdmin } from '@/lib/supabase'; // Import Supabase admin client

// 3. Retrieve Single Client (GET by ID)
export async function GET(request: NextRequest, { params }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;

  if (!clientId || typeof clientId !== 'string') {
    return NextResponse.json({ error: 'Invalid Client ID' }, { status: 400 });
  }

  // Check for query parameters to include tasks and documents
  const { searchParams } = new URL(request.url);
  const includeTasks = searchParams.get('includeTasks') === 'true';
  const includeDocuments = searchParams.get('includeDocuments') === 'true';

  try {
    // Use Prisma.ClientFindUniqueArgs for better type safety
    const findOptions: Prisma.ClientFindUniqueArgs = {
      where: {
        id: clientId,
      },
      include: {} // Initialize include object
    };

    // Conditionally include tasks
    if (includeTasks) {
      findOptions.include.tasks = {
        orderBy: {
          createdAt: 'desc', // Or sort as needed
        },
      };
      console.log(`Fetching client ${clientId} WITH tasks...`);
    }
    
    // Conditionally include documents
    if (includeDocuments) {
      findOptions.include.documents = {
        orderBy: {
            createdAt: 'desc', // Or sort as needed
        },
      };
      console.log(`Fetching client ${clientId} WITH documents...`);
    }
    
    // Remove include object if empty to avoid Prisma errors
    if (Object.keys(findOptions.include).length === 0) {
        delete findOptions.include;
    }

    const client = await prisma.client.findUnique(findOptions);

    if (!client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }

    return NextResponse.json(client);

  } catch (error) {
    console.error(`Failed to fetch client ${clientId}:`, error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

// 4. Client Update (PUT/PATCH - Placeholder)
export async function PUT(request: NextRequest, { params }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;
  // TODO: Implement PUT/PATCH logic
  // 1. Validate clientId
  // 2. Parse and validate request body (use Zod schema similar to POST)
  // 3. Use prisma.client.update() with validated data
  // 4. Handle errors (e.g., not found, validation)
  // 5. Return updated client or success message

  console.log(`Placeholder for PUT/PATCH /api/clients/${clientId}`);
  return NextResponse.json({ message: 'Update endpoint not implemented yet.', clientId }, { status: 501 }); // 501 Not Implemented
}

// 4. Client Delete (DELETE - Placeholder)
export async function DELETE(request: NextRequest, { params }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;

  if (!clientId || typeof clientId !== 'string') {
    return NextResponse.json({ error: 'Invalid Client ID' }, { status: 400 });
  }

  console.log(`Attempting to delete client ${clientId} and associated data...`);

  try {
    // Use a Prisma transaction to ensure all deletions succeed or fail together
    await prisma.$transaction(async (tx) => {
      // 1. Find related documents to get their Supabase paths
      const documentsToDelete = await tx.document.findMany({
        where: { clientId: clientId },
        select: { id: true, fileUrl: true },
      });

      // 2. Delete files from Supabase Storage
      if (documentsToDelete.length > 0) {
        const filePaths = documentsToDelete.map(doc => doc.fileUrl).filter(Boolean); // Filter out any null/empty paths
        if (filePaths.length > 0) {
            console.log(`Deleting ${filePaths.length} files from Supabase for client ${clientId}:`, filePaths);
            const { data, error } = await supabaseAdmin.storage
                .from('generated-documents') // Use your bucket name
                .remove(filePaths);
            
            if (error) {
                console.error('Supabase file deletion error:', error);
                // Decide if this should roll back the transaction
                throw new Error(`Failed to delete associated documents from storage: ${error.message}`);
            }
            console.log('Supabase file deletion result:', data);
        }
      }

      // 3. Delete related documents from Prisma (cascades should handle this if set up)
      // If cascade delete is NOT set on Document -> Client relation, delete manually:
      // await tx.document.deleteMany({ where: { clientId: clientId } });
      
      // 4. Delete related tasks from Prisma (cascades should handle this if set up)
      // If cascade delete is NOT set on Task -> Client relation, delete manually:
      // await tx.task.deleteMany({ where: { clientId: clientId } });

      // 5. Delete the client record itself
      // This will trigger cascade deletes for related records if schema is configured
      await tx.client.delete({
        where: { id: clientId },
      });
      
      console.log(`Successfully deleted client ${clientId} from database.`);
    });

    // If transaction is successful
    return new NextResponse(null, { status: 204 }); // 204 No Content is standard for successful DELETE

  } catch (error: unknown) {
    console.error(`Failed to delete client ${clientId}:`, error);

    // Handle case where client doesn't exist (prisma throws P2025)
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }
    
    const message = error instanceof Error ? error.message : "Internal Server Error during deletion";
    return NextResponse.json({ error: message }, { status: 500 });
  }
} 