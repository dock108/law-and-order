import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { z } from 'zod';

interface RouteParams {
  params: { taskId: string };
}

// Zod schema for validating the request body for task update
const taskUpdateSchema = z.object({
  status: z.enum(['Pending', 'In Progress', 'Completed', 'Overdue']), // Define allowed statuses
  // Add other updatable fields like 'notes' if needed
});

// PATCH /api/tasks/[taskId]
export async function PATCH(request: Request, { params }: RouteParams) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { taskId } = params;
  if (!taskId) {
    return NextResponse.json({ error: 'Task ID is required' }, { status: 400 });
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = taskUpdateSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    const { status } = validation.data;

    // Optional: Verify the task belongs to a client accessible by the current user
    // This requires knowing the user structure or assuming single-user setup
    // const task = await prisma.task.findUnique({ where: { id: taskId }, include: { client: true } });
    // if (!task /* || task.client.userId !== session.user.id */ ) {
    //     return NextResponse.json({ error: 'Task not found or access denied' }, { status: 404 });
    // }

    // Update the task status
    const updatedTask = await prisma.task.update({
      where: { id: taskId },
      data: {
        status: status,
        // Add other fields from validation.data if updating more than status
      },
    });

    console.log(`Updated task ${taskId} status to ${status}`);
    return NextResponse.json(updatedTask);

  } catch (error: any) {
    // Handle potential errors, like task not found during update (P2025)
    if (error instanceof Error && (error as any).code === 'P2025') {
        return NextResponse.json({ error: 'Task not found' }, { status: 404 });
    }
    console.error(`Failed to update task ${taskId}:`, error);
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
} 