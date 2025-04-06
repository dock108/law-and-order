# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - 2025-04-06

- Initialized project structure based on `implementation.md`.
- Verified and installed all core dependencies: `next-auth`, `prisma`, `@prisma/client`, `openai`, `handlebars`, `jspdf`, `bcrypt`.
- Created `CHANGELOG.md` for tracking changes.
- Created `docs/` directory for additional documentation.
- Defined Prisma schema for `Client` and `Document` models (`prisma/schema.prisma`).
- Configured SQLite database connection (`DATABASE_URL` in `.env.local`).
- Ran initial database migration (`npx prisma migrate dev --name init`) to create tables.
- Configured basic NextAuth.js authentication (`src/app/api/auth/[...nextauth]/route.ts`) using `CredentialsProvider`.
- Added `NEXTAUTH_SECRET` and `NEXTAUTH_URL` to `.env.local`.
- Added guidance on accessing sessions (server/client components) and securing API routes.
- Created basic Lawyer Dashboard UI (`src/app/dashboard/page.tsx`) with mock client list and link to `/new-client`.
- Created the New Client Intake Form (`src/app/new-client/page.tsx`) as a Client Component with state management, basic validation, and POST submission logic.
- Created API routes for Client CRUD (`src/app/api/clients/route.ts` and `src/app/api/clients/[clientId]/route.ts`):
  - Implemented `POST` (create) with Zod validation and `GET` (list all).
  - Implemented `GET` (retrieve single by ID).
  - Added placeholders for `PUT`/`PATCH` (update) and `DELETE`.
- Added shared Prisma Client instance (`src/lib/prisma.ts`).
- Installed `zod` for validation.
- Created example Handlebars template (`src/templates/demand-letter.md`).
- Created utility (`src/lib/templates.ts`) for loading, compiling, and populating Handlebars templates with formatted data.
- Added a test API route (`src/app/api/test-template/route.ts`) to demonstrate template generation with mock data.
- Created API route `src/app/api/docs/generate/route.ts` for dynamic document generation via POST, using Handlebars templates and client data, with Zod validation.
- Created API route `src/app/api/docs/modify/route.ts` to modify document content via POST using OpenAI API (`gpt-4-turbo`), taking document text and instructions.
- Added `OPENAI_API_KEY` to `.env.local` requirements.
- Created UI component/page (`src/app/doc-modifier/page.tsx`) for AI document modification, allowing text area input or file upload (.txt, .md), instruction input, and preview of the modified result.
- Created API route `src/app/api/docs/pdf/route.ts` to generate downloadable PDFs from text/markdown content using jsPDF.
- Added Supabase client library (`@supabase/supabase-js`).
- Added Supabase environment variables (`NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) to `.env.local` requirements.
- Created Supabase admin client utility (`src/lib/supabase.ts`).
- Created API route `POST /api/clients/[clientId]/documents` to:
  - Generate document from template.
  - Generate PDF using jsPDF.
  - Upload PDF to private Supabase Storage bucket.
  - Create `Document` record in Prisma linking client and storage path.
- Created API route `GET /api/documents/[documentId]/download` to generate time-limited Supabase signed URLs for secure file access.
- Added Resend SDK (`resend`).
- Added Resend environment variables (`RESEND_API_KEY`, `EMAIL_FROM_ADDRESS`) to `.env.local` requirements.
- Created API route `POST /api/email/send` to:
  - Fetch specified document details (Prisma) and PDF content (Supabase).
  - Send email via Resend with PDF as attachment. 