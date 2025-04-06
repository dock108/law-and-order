import { NextResponse } from 'next/server';
import {
  generateDocumentFromTemplate,
  prepareTemplateData,
} from '@/lib/templates';

// Mock client data (replace with actual data fetching in real route)
const mockClientData = {
  id: 'mock-client-123',
  name: 'Alice Wonderland',
  email: 'alice@example.com',
  phone: '555-123-4567',
  incidentDate: new Date('2024-02-10T00:00:00Z'), // Use Date object
  location: 'Rabbit Hole Lane',
  injuryDetails: 'Fell down a rather deep hole, bumped head.',
  medicalExpenses: 1250.75,
  insuranceCompany: 'Cheshire Cat Claims Inc.',
  lawyerNotes: 'Client seems easily confused.',
  onboardedAt: new Date(),
  updatedAt: new Date(),
};

export async function GET(request: Request) {
  try {
    // 1. Prepare data for the template
    const templateData = prepareTemplateData(mockClientData);

    // 2. Specify the template name
    const templateName = 'demand-letter'; // Matches 'demand-letter.md'

    // 3. Generate the document content
    const populatedContent = await generateDocumentFromTemplate(
      templateName,
      templateData
    );

    // 4. Return the populated content (as plain text/markdown)
    return new NextResponse(populatedContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
      },
    });

  } catch (error: any) {
    console.error('Template generation failed:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate document' },
      { status: 500 }
    );
  }
} 