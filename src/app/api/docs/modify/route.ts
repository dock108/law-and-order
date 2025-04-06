import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { z } from 'zod';
import OpenAI from 'openai';

// Initialize OpenAI client
// Ensure OPENAI_API_KEY is set in your .env.local file
if (!process.env.OPENAI_API_KEY) {
  console.warn(
    'OPENAI_API_KEY is not set. AI functionality will be disabled.'
  );
}
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Zod schema for validating the incoming request body
const modifyRequestSchema = z.object({
  document: z.string().min(10, { message: 'Document content is too short' }),
  instruction: z.string().min(5, { message: 'Modification instruction is too short' }),
});

// Recommended model for cost/performance balance
const AI_MODEL = 'gpt-4-turbo';

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check if OpenAI API key is available
  if (!process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      { error: 'AI Service is not configured by the administrator.' },
      { status: 503 } // 503 Service Unavailable
    );
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = modifyRequestSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    const { document, instruction } = validation.data;

    // Construct the prompt for OpenAI
    // Be specific to guide the AI effectively
    const prompt = `
      You are an expert legal assistant specializing in document revision.
      Modify the following document based *only* on the specific instruction provided.
      Maintain the original format (e.g., markdown) unless instructed otherwise.
      Return *only* the fully modified document content, without any introductory phrases, explanations, or conversational text.

      Instruction:
      """
      ${instruction}
      """

      Original Document:
      """
      ${document}
      """

      Modified Document:
    `;

    // Call OpenAI API
    console.log(`Calling OpenAI (${AI_MODEL}) with instruction: ${instruction}`);
    const completion = await openai.chat.completions.create({
      model: AI_MODEL,
      messages: [
        { role: 'system', content: 'You are an expert legal assistant specializing in document revision.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.5, // Adjust for creativity vs. determinism (0.0 to 1.0)
      max_tokens: 2048, // Adjust based on expected output length
    });

    const modifiedContent = completion.choices[0]?.message?.content?.trim();

    if (!modifiedContent) {
      throw new Error('AI did not return modified content.');
    }

    // 3. API Response
    return NextResponse.json({ modifiedDocument: modifiedContent });

  } catch (error: any) {
    console.error('AI document modification failed:', error);

    if (error instanceof OpenAI.APIError) {
        // Handle specific OpenAI API errors
        return NextResponse.json({ error: `OpenAI API Error: ${error.status} ${error.name}`, details: error.message }, { status: error.status || 500 });
    }

    // General error
    return NextResponse.json(
      { error: error.message || 'Failed to modify document' },
      { status: 500 }
    );
  }
} 