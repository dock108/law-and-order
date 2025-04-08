# Task Management Guide

This document explains the automatic task generation and management system within the Law & Order application.

## Overview

The application can automatically generate a predefined list of tasks for a new client based on certain intake criteria. This helps standardize workflows and ensures key steps aren't missed during client onboarding.

## Features

- **Template-Based Generation**: Tasks are generated from templates.
- **Scenario Selection**: The system attempts to select the most relevant task template based on client intake data (e.g., case type, verbal quality).
- **Automatic Creation**: Tasks are created in the database when a new client is added via the API.
- **Due Date Calculation**: Tasks can have relative due dates (e.g., "due in 7 days") which are calculated automatically.

## Task Model (Prisma)

The `Task` model defines the structure for tasks in the database:

```prisma
// prisma/schema.prisma
model Task {
  id            String   @id @default(uuid())
  clientId      String   // Foreign key
  description   String
  dueDate       DateTime?
  status        String   @default("Pending") // Pending, In Progress, Completed, Overdue
  notes         String?  // Optional field for task-specific notes
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  client        Client   @relation(fields: [clientId], references: [id])

  @@index([clientId]) // Index for faster task lookups by client
}
```

## Task Templates

- **Location**: Task list templates are stored in `src/assets/task-templates/`.
- **Format**: Templates are currently expected to be **Markdown (`.md`) files**.
- **Structure**: Each task within the Markdown file should be on its own line, formatted as:
    - `- Task description` (no specific due date)
    - `- Task description (due X days)` (due date calculated X days from creation)
    - Example line: `- Send representation letter (due 2 days)`
- **Naming Convention**: Templates should be named descriptively (e.g., `Task List - Initial (MVA Good Verbal).md`, `Task List - Generic.md`).

## Generation Logic

1.  **Trigger**: Task generation occurs automatically within the `POST /api/clients` API route after a new client record is successfully created.
2.  **Selection**: The `generateTasksForClient` function in `src/lib/tasks.ts` is called.
    - It uses the `selectTaskTemplate` internal function to choose a Markdown template file from `src/assets/task-templates/`.
    - **Note**: The current selection logic in `selectTaskTemplate` uses placeholder client data (`caseType`, `verbalQuality`). This needs to be updated to use actual data from the client intake form and potentially updated client model fields.
3.  **Parsing**: The selected Markdown file is read, and the `parseTasksFromMarkdown` function uses a regular expression (`/^\s*-\s+(.*?)(?:\s*\(due\s+(\d+)\s+days?\))?\s*$/i`) to extract the task description and optional due day offset from each line matching the expected format.
4.  **Due Date Calculation**: If an offset (e.g., `(due 7 days)`) is found, the absolute `dueDate` is calculated by adding that many days to the current date.
5.  **Database Insertion**: The extracted and formatted tasks are saved to the database using `prisma.task.createMany`, linked to the new `clientId`.

## Using the Feature

- Ensure your task list Markdown files are correctly placed in `src/assets/task-templates/` and follow the specified format.
- When a new client is created through the application's intake form (which uses `POST /api/clients`), tasks should be automatically generated.
- You will need to build UI components to display and manage these tasks (e.g., on the client detail page).

## Future Development

- **Refine Selection Logic**: Update `selectTaskTemplate` to use real client data for accurate template selection.
- **Task Management UI**: Build frontend components to view, filter, sort, and update task statuses.
- **Task Update API**: Create API endpoints (e.g., `PUT /api/tasks/[taskId]`) to allow updating task status, notes, or due dates.
- **Notifications**: Implement notifications for upcoming or overdue tasks.
- **Template Format**: Consider migrating templates to JSON for more robust parsing and structure compared to Markdown/regex.

## Related Files

- `src/lib/tasks.ts`: Core logic for selecting, parsing, and generating tasks.
- `src/app/api/clients/route.ts`: API route where task generation is triggered.
- `src/assets/task-templates/`: Directory containing the Markdown task list templates.
- `prisma/schema.prisma`: Contains the `Task` model definition. 