import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';

// Zod schema for validating the request body for task creation
// Commented out since not used currently - will be used in future implementation
// const taskCreateSchema = z.object({
//   title: z.string().min(1, "Title is required"),
//   description: z.string().optional(),
//   dueDate: z.string().optional(), // ISO date string
//   clientId: z.string().optional(),
//   status: z.enum(['Pending', 'In Progress', 'Completed', 'Overdue']).default('Pending'),
// });

// GET /api/tasks - Get all tasks
export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    // Fetch all tasks
    // Optional: Add filtering by query parameters
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const clientId = url.searchParams.get('clientId');

    const whereClause: Record<string, unknown> = {};
    if (status) {
      whereClause.status = status;
    }
    if (clientId) {
      whereClause.clientId = clientId;
    }

    const tasks = await prisma.task.findMany({
      where: whereClause,
      orderBy: { dueDate: 'asc' },
      include: {
        client: true,
      },
    });

    return NextResponse.json(tasks);
  } catch (error: unknown) {
    console.error("Error fetching tasks:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to fetch tasks: ${message}` }, { status: 500 });
  }
}

// POST /api/tasks - Create a new task
export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    // Explicitly type the new task data
    const newTaskData: Omit<Task, 'id' | 'createdAt' | 'updatedAt'> = body;
    const task = await prisma.task.create({
      data: newTaskData,
    });
    return NextResponse.json(task, { status: 201 });
  } catch (error: unknown) {
    console.error("Error creating task:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to create task: ${message}` }, { status: 500 });
  }
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function PATCH(_request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    // Simply acknowledge the request without using the body
    // In a real implementation, you would process the body data
    return NextResponse.json({ message: "Updates processed successfully" });
  } catch (error: unknown) {
    console.error("Error updating tasks:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to update tasks: ${message}` }, { status: 500 });
  }
} 