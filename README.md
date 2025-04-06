# Law & Order - Legal Document Automation

A Next.js application for law firms to automate client onboarding, document generation, and management.

## Features

- **Client Management**: Add and manage client information
- **Document Generation**: Automatically generate legal documents from templates
- **Document Storage**: Store documents securely with Supabase
- **PDF Generation**: Convert documents to PDF format
- **Email Integration**: Send generated documents via email
- **AI Assistance**: Modify documents using AI (OpenAI GPT integration)

## Setup

1. **Clone the repository**

```bash
git clone [repository-url]
cd law-and-order
```

2. **Install dependencies**

```bash
npm install
```

3. **Set up environment variables**

Create a `.env.local` file with the following variables:

```
# Authentication
NEXTAUTH_SECRET=your_secure_random_string
NEXTAUTH_URL=http://localhost:3000

# Database
DATABASE_URL="file:./dev.db"

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM_ADDRESS=your_sender_email@example.com
```

4. **Set up the database**

```bash
npx prisma migrate dev --name init
```

5. **Create Supabase storage bucket**

Create a private bucket named `generated-documents` in your Supabase project.

6. **Run the development server**

```bash
npm run dev
```

7. **Login credentials**

- Username: `lawyer`
- Password: `password123`

## Document Templates

Templates are stored in the `src/templates` directory as Markdown files with Handlebars syntax for variable interpolation.

## Markdown Processing

The application processes Markdown formatting when generating PDFs to ensure proper formatting:

- Headings are converted to uppercase text
- Bold and italic formatting is preserved in the content
- Lists (bullet points and numbered) are properly formatted
- Links are included as text
- Tables are simplified for PDF generation

## API Routes

- `/api/clients` - Client management
- `/api/clients/[clientId]/documents` - Document management for a specific client
- `/api/docs/generate` - Document generation from templates
- `/api/docs/modify` - AI-assisted document modification
- `/api/docs/pdf` - PDF generation
- `/api/documents/[documentId]/download` - Document download with signed URLs
- `/api/email/send` - Email documents to recipients

## Technologies

- Next.js (App Router)
- Prisma ORM
- NextAuth.js for authentication
- Supabase for storage
- jsPDF for PDF generation
- OpenAI for document modifications
- Resend for email delivery
- Handlebars for template processing
- Tailwind CSS for styling

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
