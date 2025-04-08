import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { z } from 'zod';

// Zod schema for validating the request body for task creation
const taskCreateSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().optional(),
  dueDate: z.string().optional(), // ISO date string
  clientId: z.string().optional(),
  status: z.enum(['Pending', 'In Progress', 'Completed', 'Overdue']).default('Pending'),
});

// GET /api/tasks - Get all tasks
export async function GET(request: Request) {
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

    const whereClause: any = {};
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
  } catch (error: any) {
    console.error('Failed to fetch tasks:', error);
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// POST /api/tasks - Create a new task
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = taskCreateSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    const taskData = validation.data;

    // Create the task
    const task = await prisma.task.create({
      data: taskData,
    });

    console.log(`Created new task: ${task.id}`);
    return NextResponse.json(task, { status: 201 });

  } catch (error: any) {
    console.error('Failed to create task:', error);
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
} 