# Law & Order - Client & Task Management App

This is a Next.js application designed for law firms (initially tailored for personal injury in NJ) to manage clients, tasks, and automatically generate standard legal documents.

## Features

*   **Client Management:** Add, view, and manage client information including contact details, case specifics (type, verbal quality), incident details, and notes.
*   **Task Management:** Create, view, and update tasks associated with clients. Tasks include descriptions, due dates, status (Pending, In Progress, Completed, Overdue), and notes.
*   **Dashboard:** Centralized view of clients and their associated tasks.
*   **Automated Document Generation:** Automatically generates standard documents (e.g., Demand Letter, Representation Letter) upon client creation using templates and populates them with client data.
*   **Automated Task Generation:** Automatically generates relevant tasks based on client case type upon creation.
*   **PDF Handling:** Integrates PDF letterhead for branding and uploads generated documents to Supabase Storage.
*   **Authentication:** Uses NextAuth.js for user authentication.
*   **Database:** Uses Prisma with a SQLite database for data persistence.

## Tech Stack

*   **Framework:** Next.js (App Router)
*   **Styling:** Tailwind CSS
*   **Database ORM:** Prisma
*   **Database:** SQLite
*   **Authentication:** NextAuth.js
*   **File Storage:** Supabase Storage
*   **PDF Generation:** `pdf-lib`
*   **Document Templating:** Handlebars (via custom logic in `@/lib/templates`)
*   **Data Validation:** Zod
*   **Utility:** Faker.js (for seeding)

## Project Structure

```
/law-and-order
|-- prisma/              # Prisma schema, migrations, and database file
|   |-- migrations/
|   |-- dev.db
|   |-- schema.prisma
|-- public/              # Static assets (images, letterhead PDF)
|-- scripts/             # Utility scripts (e.g., database seeding)
|   |-- seed-database.ts
|   |-- seed.sh
|-- src/
|   |-- app/             # Next.js App Router directory
|   |   |-- api/         # API routes (auth, clients, tasks, documents)
|   |   |-- dashboard/   # Dashboard page and layout
|   |   |-- clients/     # Client listing/details pages (structure TBD)
|   |   |-- new-client/  # Page and layout for adding new clients
|   |   |-- (other routes...)
|   |   |-- layout.tsx   # Root layout
|   |   |-- page.tsx     # Root page (e.g., landing or redirect)
|   |   |-- globals.css
|   |-- assets/          # Source assets (e.g., original letterhead)
|   |-- components/      # Reusable React components (TaskList, Letterhead, etc.)
|   |-- lib/             # Core logic, utilities, libraries config
|   |   |-- prisma.ts    # Prisma client instance
|   |   |-- supabase.ts  # Supabase client instance
|   |   |-- templates.ts # Document generation logic
|   |   |-- tasks.ts     # Task generation logic
|-- .env.local           # Local environment variables (ignored by git)
|-- .gitignore
|-- next.config.mjs
|-- package.json
|-- tailwind.config.ts
|-- tsconfig.json
|-- README.md            # This file
```

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd law-and-order
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up Environment Variables:**
    *   Create a `.env.local` file in the root directory.
    *   Add the following variables (replace placeholders with actual values):
        ```env
        DATABASE_URL="file:/path/to/your/project/law-and-order/prisma/dev.db" # Use absolute path
        NEXTAUTH_URL="http://localhost:3000"
        NEXTAUTH_SECRET="<generate_a_strong_secret>" # Generate with: openssl rand -base64 32
        
        # Supabase (for document storage)
        NEXT_PUBLIC_SUPABASE_URL="<your_supabase_project_url>"
        SUPABASE_SERVICE_ROLE_KEY="<your_supabase_service_role_key>"
        
        # OpenAI (if using for template generation)
        # OPENAI_API_KEY="<your_openai_api_key>"
        
        # Resend (if using for email)
        # RESEND_API_KEY="<your_resend_api_key>"
        # EMAIL_FROM_ADDRESS="Your Name <you@example.com>"
        ```
    *   **Important:** Ensure the `DATABASE_URL` uses an **absolute path** to your `prisma/dev.db` file to avoid issues with Prisma finding the database.
    *   Make sure you have a Supabase project set up with a bucket named `generated-documents` (or update `BUCKET_NAME` constant in `src/app/api/clients/route.ts`).

4.  **Set up the Database:**
    *   Run Prisma migrations to create the database schema:
        ```bash
        npx prisma migrate dev --name init
        ```

5.  **Seed the Database (Optional):**
    *   To populate the database with sample client and task data:
        ```bash
        npm run seed:db 
        # or
        ./scripts/seed.sh
        ```

6.  **Run the Development Server:**
    ```bash
    npm run dev
    ```
    The application should now be running at http://localhost:3000.

## Available Scripts

*   `npm run dev`: Starts the Next.js development server.
*   `npm run build`: Builds the application for production.
*   `npm run start`: Starts the production server.
*   `npm run lint`: Lints the codebase.
*   `npm run seed:db`: Seeds the database with sample data using `ts-node`.
*   `npx prisma migrate dev`: Creates and applies database migrations.
*   `npx prisma studio`: Opens Prisma Studio to view/edit database data.

## Key Concepts & Implementation Details

*   **API Routes:** Handle backend logic for authentication, data fetching/mutation (clients, tasks), and document generation.
*   **Server Components:** Used for data fetching directly on the server (e.g., Dashboard page fetching clients).
*   **Client Components:** Used for interactive UI elements (forms, task list updates) - marked with `'use client';`.
*   **Document Generation Flow (POST /api/clients):**
    1.  Client data validated via Zod.
    2.  Client created in Prisma.
    3.  Default document templates are processed (`generateDocumentFromTemplate`).
    4.  Markdown content is prepared for PDF (`processMarkdownForPDF`).
    5.  Letterhead PDF is loaded.
    6.  Content is drawn onto the letterhead using `pdf-lib`.
    7.  Generated PDF is uploaded to Supabase Storage.
    8.  Document record is created in Prisma linking to the Supabase file.
*   **Task Generation Flow (POST /api/clients):**
    1.  After client creation, `generateTasksForClient` is called.
    2.  This function (likely in `lib/tasks.ts`) determines relevant tasks based on `caseType`, `verbalQuality`, etc.
    3.  Tasks are created in bulk using `prisma.task.createMany`.
