# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Added a general API route `src/app/api/tasks/route.ts` for listing (`GET`) and creating (`POST`) tasks.
- Added database seeding script (`scripts/seed-database.ts` and `scripts/seed.sh`) using `@faker-js/faker` to populate clients, tasks, and documents.
- Added `seed:db` script to `package.json`.
- Added `ts-node` and `@faker-js/faker` as dev dependencies.
- Added `.env.local` for local environment configuration and removed `.env` (added `.env` to `.gitignore`).
- Added basic `Letterhead` component (`src/components/Letterhead.tsx`).
- Added layout files for `/dashboard`, `/clients`, and `/new-client` routes.
- Added "Back to Dashboard" button on the `/new-client` page.
- Added "Revert" button to completed tasks in the `TaskList` component, allowing status change back to "In Progress".
- Added `automationType` (String?), `requiresDocs` (Boolean?), and `automationConfig` (String?) fields to the `Task` model in `prisma/schema.prisma` to support task-specific automation actions.
- Updated the database seeding script (`scripts/seed-database.ts`) to populate sample automation data for specific task types (e.g., 'Send demand letter', 'Contact insurance company', 'Research similar cases').
- Added `AutomationModal` component (`src/components/AutomationModal.tsx`) to display a confirmation prompt before starting a task automation.
- Integrated the `AutomationModal` into `TaskList` (`src/components/TaskList.tsx`); clicking the '⚡️ Action' button now opens this modal.
- Created base API route `src/app/api/automation/route.ts` with auth, validation, and placeholder logic for handling automation POST requests.
- Connected `TaskList` to call the `/api/automation` endpoint via `handleAutomationStart`.
- Enhanced `AutomationModal` to show loading, success, and error states based on API response.
- Implemented specific automation logic for `INITIAL_CONSULT` task type in `/api/automation`: 
    - Added `INITIAL_CONSULT` to Zod schema and seed script.
    - Created `src/templates/initial-consult-email.md`.
    - Fetches client data, generates email body from template, and calls placeholder ChatGPT function for suggestions.
    - Returns drafted email and suggestions in the response payload.
- Updated `AutomationModal` to display combined email draft and suggestions for `INITIAL_CONSULT` results.
- Implemented specific automation logic for `CHATGPT_SUGGESTION` task type (config: `legal_research`) in `/api/automation`:
    - Added `legal_research` config to seed script for "Research applicable laws" task.
    - Created placeholder `getLegalResearchSuggestions` function simulating AI call based on `client.caseType`.
    - API route now differentiates CHATGPT suggestions based on `automationConfig`.
- Replaced placeholder AI functions (`getConsultSuggestions`, `getLegalResearchSuggestions`) in `src/app/api/automation/route.ts` with actual OpenAI API calls (`gpt-4-turbo-preview`).
- Added OpenAI client initialization and basic error handling for API calls.
- Updated `CHATGPT_SUGGESTION` case to use `gpt-3.5-turbo` for generic suggestions.
- Added try/catch block around the main `switch` statement in the API route to handle automation-specific errors.
- Created `src/lib/documents.ts` with a reusable `generateAndStorePdf` function encapsulating pdf-lib generation and Supabase upload logic.
- Refactored client creation route (`POST /api/clients`) to use `generateAndStorePdf`.
- Implemented `DOC_GENERATION` automation logic in `/api/automation`:
    - Uses `automationConfig` to determine the template name.
    - Calls `generateDocumentFromTemplate` and `generateAndStorePdf`.
    - Returns generated document info (ID, path) in the response.
- Updated `AutomationModal` to display document generation results, including a placeholder link for download/view.
- Implemented specific `EMAIL_DRAFT` logic for config `client_follow_up` in `/api/automation`:
    - Added `client_follow_up` config to seed script for "Follow up with client" task.
    - API route now generates a specific follow-up email template.
    - Added TODO comments for logging communication and updating task status.
- Implemented database updates within `/api/automation` route:
    - Witness interview questions (from AI) are now saved to the associated task's notes field.
    - Client follow-up email drafts now log a message to task notes and update task status to 'Awaiting Response'.
    - Successful document generation now updates task status to 'Completed'.
    - DB updates are collected and run via `Promise.all()` after automation logic.
- Enhanced `EMAIL_DRAFT` automation in `/api/automation`:
    - Added `Resend` SDK initialization (conditional on `RESEND_API_KEY`).
    - Added `wrapWithHtmlLetterhead` helper function for basic HTML email structure.
    - If Resend is configured, sends email directly using Resend SDK with HTML letterhead wrapper.
    - If Resend is not configured, generates a `mailto:` link with plain text body.
    - Task status is updated appropriately ('Completed' for send, 'Awaiting User Action' for mailto).
    - Includes check for client email address before attempting send/draft.
- Refined OpenAI prompts in `/api/automation` helper functions to include more context and explicit AI disclaimers.
- Added TODO comments for logging OpenAI prompts and responses.
- Updated `CHATGPT_SUGGESTION` and `INITIAL_CONSULT` automations to set task status to 'Completed' upon successful generation of suggestions/drafts.

### Changed

- Refactored task API structure: Removed dynamic `[taskId]` route in favor of the general `tasks/route.ts` for PATCH operations and the new route for GET/POST.
- Updated `.gitignore` with more comprehensive rules for Node, Next.js, OS, IDEs, database, and environment files.
- Updated `README.md` with detailed project structure, setup instructions (including absolute `DATABASE_URL`), tech stack, available scripts, and key concept explanations.
- Integrated letterhead PDF directly into the `/dashboard` page using an `<iframe>` instead of a shared layout component.
- Updated `TaskList` component to include the Revert button logic.
- Fixed newline handling in `wrapWithHtmlLetterhead` function.

### Fixed

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

## [DATE - e.g., 2025-04-08] - Previous Release (Example)

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
- Verified and installed all core dependencies: `next-auth`, `prisma`, `@prisma/client`, `openai`, `handlebars`, `