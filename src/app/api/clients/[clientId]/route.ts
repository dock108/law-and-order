import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';

interface RouteParams {
  params: { clientId: string };
}

// 3. Retrieve Single Client (GET by ID)
export async function GET(request: NextRequest, { params }: RouteParams) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;

  if (!clientId || typeof clientId !== 'string') {
    return NextResponse.json({ error: 'Invalid Client ID' }, { status: 400 });
  }

  // Check for query parameter to include tasks
  const { searchParams } = new URL(request.url);
  const includeTasks = searchParams.get('includeTasks') === 'true';

  try {
    const findOptions: Parameters<typeof prisma.client.findUnique>[0] = {
      where: {
        id: clientId,
      },
    };

    // Conditionally include tasks based on query param
    if (includeTasks) {
        findOptions.include = {
            tasks: {
                orderBy: {
                    dueDate: 'asc',
                },
            },
        };
        console.log(`Fetching client ${clientId} WITH tasks...`);
    } else {
        console.log(`Fetching client ${clientId} without tasks...`);
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
export async function PUT(request: NextRequest, { params }: RouteParams) {
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
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { clientId } = params;
  // TODO: Implement DELETE logic
  // 1. Validate clientId
  // 2. Consider implications: What happens to related Documents?
  //    - Delete them? (Cascade delete - configure in Prisma schema or handle manually)
  //    - Disassociate them? (Set clientId to null - requires schema change)
  // 3. Use prisma.client.delete() or prisma.client.update() (for soft delete)
  // 4. Handle errors (e.g., not found)
  // 5. Return success message or status code (e.g., 204 No Content)

  console.log(`Placeholder for DELETE /api/clients/${clientId}`);
  return NextResponse.json({ message: 'Delete endpoint not implemented yet.', clientId }, { status: 501 }); // 501 Not Implemented
} 