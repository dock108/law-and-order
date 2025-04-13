import { NextResponse, NextRequest } from 'next/server';
import { getServerSession } from 'next-auth/next';
import prisma from '@/lib/prisma';
import { z } from 'zod';

// Zod schema for validating the request body for PATCH
const taskUpdateSchema = z.object({
  status: z.string().optional(), // Allow updating only status for now
  // Add other fields as needed (e.g., description, dueDate)
});

// PATCH /api/tasks/[taskId]
export async function PATCH(request: Request, { params }) {
  const session = await getServerSession();
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

  } catch (error: unknown) {
    // Handle potential errors, like task not found during update (P2025)
    if (error instanceof Error && 'code' in error && error.code === 'P2025') {
        return NextResponse.json({ error: 'Task not found' }, { status: 404 });
    }
    console.error(`Failed to update task ${taskId}:`, error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to update task: ${message}` }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { taskId: string } }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { taskId } = params;
  if (!taskId) {
    return NextResponse.json({ error: 'Task ID is required' }, { status: 400 });
  }

  try {
    // Optional: Verify the task belongs to a client accessible by the current user
    // This requires knowing the user structure or assuming single-user setup
    // const task = await prisma.task.findUnique({ where: { id: taskId }, include: { client: true } });
    // if (!task /* || task.client.userId !== session.user.id */ ) {
    //     return NextResponse.json({ error: 'Task not found or access denied' }, { status: 404 });
    // }

    // Delete the task
    const deletedTask = await prisma.task.delete({
      where: { id: taskId },
    });

    console.log(`Deleted task ${taskId}`);
    return NextResponse.json(deletedTask);

  } catch (error: unknown) {
    console.error(`Error deleting task ${taskId}:`, error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to delete task: ${message}` }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, { params }: { params: { taskId: string } }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { taskId } = params;
  if (!taskId) {
    return NextResponse.json({ error: 'Task ID is required' }, { status: 400 });
  }

  try {
    const body = await request.json();
    // Explicitly type the update data (adjust fields as needed)
    const updatedTaskData: Partial<Pick<Task, 'description' | 'dueDate' | 'status' | 'notes'>> = body;

    const updatedTask = await prisma.task.update({
      where: { id: taskId },
      data: updatedTaskData,
    });
    return NextResponse.json(updatedTask);
  } catch (error: unknown) {
    console.error(`Failed to update task ${taskId}:`, error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: `Failed to update task: ${message}` }, { status: 500 });
  }
} 