# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - 2025-04-09 (Assumed Date)

- Added a general API route `src/app/api/tasks/route.ts` for listing (`GET`) and creating (`POST`) tasks.
- Added database seeding script (`scripts/seed-database.ts` and `scripts/seed.sh`) using `@faker-js/faker` to populate clients, tasks, and documents.
- Added `seed:db` script to `package.json`.
- Added `ts-node` and `@faker-js/faker` as dev dependencies.
- Added `.env.local` for local environment configuration and removed `.env` (added `.env` to `.gitignore`).
- Added basic `Letterhead` component (`src/components/Letterhead.tsx`).
- Added layout files for `/dashboard`, `/clients`, and `/new-client` routes.
- Added "Back to Dashboard" button on the `/new-client` page.
- Added "Revert" button to completed tasks in the `TaskList` component, allowing status change back to "In Progress".

### Changed - 2025-04-09 (Assumed Date)

- Refactored task API structure: Removed dynamic `[taskId]` route in favor of the general `tasks/route.ts` for PATCH operations and the new route for GET/POST.
- Updated `.gitignore` with more comprehensive rules for Node, Next.js, OS, IDEs, database, and environment files.
- Updated `README.md` with detailed project structure, setup instructions (including absolute `DATABASE_URL`), tech stack, available scripts, and key concept explanations.
- Integrated letterhead PDF directly into the `/dashboard` page using an `<iframe>` instead of a shared layout component.
- Updated `TaskList` component to include the Revert button logic.

### Fixed - 2025-04-09 (Assumed Date)

- Resolved Prisma database path issues by using an absolute path in `DATABASE_URL` within `.env.local`.
- Fixed issues running `npx prisma migrate dev` and `npm run seed:db` related to environment variables and database location.
- Addressed `@faker-js/faker` deprecation warnings in the seed script.
- Resolved module type conflicts (`type: module` vs CommonJS) preventing `ts-node` from running the seed script.
- Fixed `headers().get()` usage in `/dashboard/page.tsx` by adding `await`.
- Corrected the `Link` component structure for the "Add New Client" button on the dashboard page.
- Fixed client creation API (`POST /api/clients`):
  - Improved error handling in the frontend form (`/new-client/page.tsx`) to correctly parse and display API error messages.
  - Enhanced the final `catch` block in the API route to return more specific error messages from document/task generation steps.
  - Added missing `caseType` and `verbalQuality` fields to the Zod validation schema (`clientSchema`).
  - Ensured `caseType` and `verbalQuality` are passed to the `prisma.client.create` call.

### Added - 2025-04-08 (Assumed Date)

- Integrated PDF letterhead using `pdf-lib`:
  - Replaced `jsPDF` with `pdf-lib` for PDF generation in document creation routes.
  - Added logic to load a letterhead PDF (`src/assets/v1_Colacci-Letterhead.pdf`) and overlay generated Markdown content onto it.
  - Included basic text wrapping and page handling within `pdf-lib`.
- Added ZIP packaging feature:
  - Installed `jszip` dependency.
  - Created API route `POST /api/docs/zip` to bundle multiple documents.
  - Route accepts `clientId` or `documentIds`, fetches PDFs from Supabase, and returns a ZIP archive.
- Added Task Management system:
  - Defined `Task` model in `prisma/schema.prisma` with relation to `Client`.
  - Ran migration `add-tasks` to update the database.
  - Created task template directory `src/assets/task-templates/`.
  - Implemented task template parsing logic (Markdown format) in `src/lib/tasks.ts`.
  - Integrated automatic task generation into the client creation API route (`POST /api/clients`).
  - Updated client creation response to include info on generated tasks.

### Added - 2025-04-07

- Improved Markdown processing for PDF generation with the `processMarkdownForPDF` function in `src/lib/templates.ts`.
- Enhanced PDF generation to properly handle Markdown formatting, including:
  - Converting headings to uppercase text
  - Removing Markdown syntax for bold and italic formatting
  - Converting bullet points to bullet characters
  - Preserving numbered lists
  - Removing link syntax while keeping the text
  - Properly handling blockquotes and code blocks
  - Simplifying tables for PDF output
  - Maintaining proper spacing between paragraphs
- Updated document generation routes to use improved Markdown processing:
  - `src/app/api/clients/[clientId]/documents/route.ts`
  - `src/app/api/clients/route.ts`
- Added comprehensive project documentation in the README.md

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