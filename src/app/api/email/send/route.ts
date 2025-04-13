import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import prisma from '@/lib/prisma';
import { supabaseAdmin } from '@/lib/supabase';
import { Resend } from 'resend';
import { z } from 'zod';

// Initialize Resend client
if (!process.env.RESEND_API_KEY) {
  console.warn('RESEND_API_KEY is not set. Email functionality will be disabled.');
}
if (!process.env.EMAIL_FROM_ADDRESS) {
  console.warn(
    'EMAIL_FROM_ADDRESS is not set. Emails may fail to send or land in spam.'
  );
}
const resend = new Resend(process.env.RESEND_API_KEY);

// Zod schema for validating the incoming request body
const emailRequestSchema = z.object({
  documentId: z.string().uuid({ message: 'Valid documentId is required' }),
  toEmail: z.string().email({ message: 'Invalid recipient email address' }),
  subject: z.string().min(1, { message: 'Subject cannot be empty' }),
  message: z.string().min(1, { message: 'Message body cannot be empty' }), // Plain text or basic HTML
});

const BUCKET_NAME = 'generated-documents'; // Match your Supabase bucket name

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check if Resend is configured
  if (!process.env.RESEND_API_KEY || !process.env.EMAIL_FROM_ADDRESS) {
    return NextResponse.json(
      { error: 'Email Service is not configured by the administrator.' },
      { status: 503 } // 503 Service Unavailable
    );
  }

  try {
    const rawData = await request.json();

    // Validate request body
    const validation = emailRequestSchema.safeParse(rawData);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid input', details: validation.error.flatten().fieldErrors },
        { status: 400 }
      );
    }
    const { documentId, toEmail, subject, message } = validation.data;

    // 1. Fetch Document record to get the file path
    const document = await prisma.document.findUnique({
      where: { id: documentId },
      include: { client: true }, // Include client to get their name for filename
    });

    if (!document) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }
    if (!document.client) {
      return NextResponse.json({ error: 'Client associated with document not found' }, { status: 404 });
    }

    // --- Optional: Authorization check ---
    // Ensure logged-in user can access this client's document
    // Add your logic here if needed for multi-user scenarios

    const filePath = document.fileUrl; // Path stored in DB

    // 2. Download the PDF content from Supabase Storage
    console.log(`Downloading from Supabase bucket '${BUCKET_NAME}' path: ${filePath}`);
    const { data: fileData, error: downloadError } =
      await supabaseAdmin.storage.from(BUCKET_NAME).download(filePath);

    if (downloadError) {
      console.error('Supabase Download Error:', downloadError);
      throw new Error(`Failed to retrieve document for sending: ${downloadError.message}`);
    }
    if (!fileData) {
        throw new Error('Downloaded file data is empty.');
    }

    // Convert Blob to Buffer (needed for Resend attachment)
    const pdfBuffer = Buffer.from(await fileData.arrayBuffer());

    // Construct a meaningful filename for the attachment
    const attachmentFilename = `${document.documentType}_${document.client.name.replace(/ /g, '_')}_${document.id.substring(0, 8)}.pdf`;

    // 3. Send Email using Resend
    console.log(`Sending email to ${toEmail} from ${process.env.EMAIL_FROM_ADDRESS}`);
    const { data: emailSentData, error: emailError } = await resend.emails.send({
      from: process.env.EMAIL_FROM_ADDRESS!, // Assert non-null as checked above
      to: [toEmail],
      subject: subject,
      // Use 'html' for richer content or 'text' for plain text
      html: `<p>${message.replace(/\n/g, '<br>')}</p>`, // Basic conversion of newlines to <br>
      // text: message, // Use this for plain text emails
      attachments: [
        {
          filename: attachmentFilename,
          content: pdfBuffer, // Attach the PDF buffer
        },
      ],
    });

    if (emailError) {
      console.error('Resend API Error:', emailError);
      throw new Error(`Failed to send email: ${emailError.message}`);
    }

    console.log('Email sent successfully:', emailSentData);

    return NextResponse.json({ success: true, message: 'Email sent successfully.', emailId: emailSentData?.id });

  } catch (error: unknown) {
    console.error('Error sending email:', error);
    const message = error instanceof Error ? error.message : 'Unknown error sending email';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
} 