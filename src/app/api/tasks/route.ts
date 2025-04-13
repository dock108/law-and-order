import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
// import { authOptions } from '@/app/api/auth/[...nextauth]/route'; // Removed import
import prisma from '@/lib/prisma';
import { z } from 'zod';

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
  const session = await getServerSession(); // Removed authOptions
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
  const session = await getServerSession(); // Removed authOptions
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

// Implement proper PATCH functionality to update tasks
export async function PATCH(request: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const data = await request.json();
    
    // Validate input
    const taskSchema = z.object({
      id: z.string(),
      status: z.enum(['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED']).optional(),
      dueDate: z.string().datetime().optional(),
      notes: z.string().optional(),
    });
    
    const validatedData = taskSchema.parse(data);
    
    // Update task in database
    const updatedTask = await prisma.task.update({
      where: { id: validatedData.id },
      data: {
        status: validatedData.status,
        dueDate: validatedData.dueDate ? new Date(validatedData.dueDate) : undefined,
        notes: validatedData.notes,
      },
    });
    
    return NextResponse.json(updatedTask);
  } catch (error) {
    console.error("Error updating task:", error);
    return NextResponse.json(
      { error: "Failed to update task" },
      { status: 500 }
    );
  }
} 