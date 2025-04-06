# Setup Guide

This guide provides detailed instructions for setting up the Law & Order document automation application.

## Prerequisites

- Node.js (v18 or later)
- npm (v8 or later)
- Git
- Supabase account
- OpenAI API key
- Resend API key

## Step 1: Clone the Repository

```bash
git clone [repository-url]
cd law-and-order
```

## Step 2: Install Dependencies

```bash
npm install
```

## Step 3: Set Up Environment Variables

Create a `.env.local` file in the root directory with the following variables:

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

### Notes on Environment Variables

- `NEXTAUTH_SECRET`: Generate a secure random string (e.g., using `openssl rand -base64 32`)
- `NEXTAUTH_URL`: Set to `http://localhost:3000` for local development or your actual domain in production
- `DATABASE_URL`: Default uses SQLite for local development
- `OPENAI_API_KEY`: Get this from your OpenAI account dashboard
- `NEXT_PUBLIC_SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: Get these from your Supabase project settings
- `RESEND_API_KEY`: Get this from your Resend account
- `EMAIL_FROM_ADDRESS`: The email address from which documents will be sent

## Step 4: Set Up the Database

Initialize the database with Prisma:

```bash
npx prisma migrate dev --name init
```

This will:
1. Create the SQLite database file (`prisma/dev.db`)
2. Run the migration to create the necessary tables
3. Generate the Prisma client

## Step 5: Set Up Supabase Storage

1. Log in to your Supabase dashboard
2. Navigate to Storage in the left sidebar
3. Create a new bucket named `generated-documents`
4. Set the bucket to private (not public)
5. Configure CORS settings if necessary

## Step 6: Prepare Authentication

The application uses a simple credentials-based authentication with a hardcoded lawyer user. For production, consider implementing a more secure authentication method.

The default login credentials are:
- Username: `lawyer`
- Password: `password123`

## Step 7: Run the Development Server

Start the development server:

```bash
npm run dev
```

The application should now be running at [http://localhost:3000](http://localhost:3000).

## Step 8: Initial Testing

1. Navigate to [http://localhost:3000](http://localhost:3000)
2. Log in with the default credentials
3. Add a test client
4. Verify that documents are automatically generated
5. Test document download and email functionality

## Troubleshooting

- **Database Issues**: If you encounter database issues, try running `npx prisma migrate reset` to reset your database
- **Supabase Connection**: Verify your Supabase credentials and ensure the storage bucket has been created
- **PDF Generation**: If PDFs aren't generating properly, check console logs for errors
- **Email Sending**: Make sure your Resend API key is valid and the sender email is configured correctly

## Next Steps

- Customize document templates in the `src/templates` directory
- Add additional template types as needed
- Configure user authentication for your specific requirements 