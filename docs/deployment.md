# Deployment Guide

This guide explains how to deploy the Law & Order application to Vercel.

## Prerequisites

- A Vercel account
- Git repository with your project
- Supabase project set up
- OpenAI API key
- Resend API key

## Step 1: Prepare Your Project for Deployment

Ensure your project is ready for deployment by:

1. Making sure all environment variables are properly referenced
2. Testing the application locally (`npm run dev`)
3. Committing all changes to your Git repository

## Step 2: Install the Vercel CLI (Optional)

If you prefer deploying via command line, install the Vercel CLI:

```bash
npm install -g vercel
```

## Step 3: Deploy Using Vercel CLI (Option A)

1. Navigate to your project directory:

```bash
cd /path/to/law-and-order
```

2. Run the Vercel deployment command:

```bash
vercel
```

3. Follow the prompts to:
   - Log in to your Vercel account (if not already logged in)
   - Link to an existing project or create a new one
   - Confirm deployment settings

## Step 4: Deploy Using Vercel Dashboard (Option B)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Import your Git repository
4. Configure project settings
5. Click "Deploy"

## Step 5: Configure Environment Variables

1. In the Vercel dashboard, navigate to your project
2. Go to "Settings" → "Environment Variables"
3. Add the following environment variables:

```
# Authentication
NEXTAUTH_SECRET=your_secure_random_string
NEXTAUTH_URL=https://your-deployed-url.vercel.app

# Database
DATABASE_URL=your_production_database_url

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM_ADDRESS=your_sender_email@example.com
```

> **Note**: For `DATABASE_URL`, you'll need to set up a production-ready database like PostgreSQL, as SQLite won't work in the serverless environment. Services like Supabase, Railway, or Neon provide PostgreSQL databases that work well with Vercel.

## Step 6: Update NextAuth Configuration (if needed)

If you're using a different authentication method in production, update the `authOptions` in `src/app/api/auth/[...nextauth]/route.ts` accordingly.

## Step 7: Set Up a Production Database

1. Create a PostgreSQL database (using Supabase, Railway, Neon, etc.)
2. Update the `DATABASE_URL` environment variable in Vercel
3. Run the Prisma migrations on your production database:

```bash
# Run all migrations needed for production
DATABASE_URL=your_production_database_url npx prisma migrate deploy
```

> **Note**: `prisma migrate deploy` applies all pending migrations. Ensure your production `DATABASE_URL` is set correctly in Vercel environment variables.

## Step 8: Create the Supabase Storage Bucket

1. In your Supabase project dashboard, go to "Storage"
2. Create a bucket named `generated-documents`
3. Set the bucket permissions to private
4. Configure any necessary CORS settings for your production domain

## Step 9: Verify Deployment

1. Visit your deployed application (e.g., `https://your-app.vercel.app`)
2. Test all functionality:
   - Login
   - Client creation
   - Document generation
   - PDF downloads
   - Email sending

## Step 10: Set Up Custom Domain (Optional)

1. In the Vercel dashboard, go to "Settings" → "Domains"
2. Add your custom domain
3. Follow the instructions to configure DNS settings

## Continuous Deployment

Once set up, Vercel will automatically deploy updates whenever you push changes to your connected Git repository:

1. Make changes to your code
2. Commit and push to your repository
3. Vercel will automatically build and deploy the changes

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:
- Verify your `DATABASE_URL` is correct
- Check if your database allows connections from Vercel's IP range
- Try using connection pooling if necessary

### API Routes Failures

If API routes fail:
- Check Vercel Function Logs in the dashboard
- Verify environment variables are correctly set
- Ensure your code is compatible with serverless functions

### PDF Generation Issues

If PDF generation doesn't work in production:
- Check if all dependencies (`pdf-lib`) are properly installed
- Ensure the functions aren't timing out (PDF generation/manipulation can be resource-intensive)
- Verify the letterhead PDF (`src/assets/v1_Colacci-Letterhead.pdf`) is included in the deployment and accessible.
- Check Vercel Function logs for errors from `pdf-lib`.

### Storage Problems

If document storage fails:
- Verify Supabase credentials
- Check if the storage bucket exists and is properly configured
- Ensure the service role key has the necessary permissions

### Task Generation Issues

If automatic tasks are not created:
- Check Vercel Function logs for the `POST /api/clients` endpoint.
- Ensure task template files in `src/assets/task-templates/` are included in the deployment.
- Verify the logic for selecting and parsing templates in `src/lib/tasks.ts` is working correctly in the serverless environment.

## Best Practices for Production

1. **Caching**: Implement caching for frequently accessed data
2. **Error Logging**: Set up proper error logging (consider using Sentry or similar)
3. **Rate Limiting**: Implement rate limiting for API routes
4. **Analytics**: Add analytics to track usage
5. **Monitoring**: Set up uptime monitoring for your application
6. **Backups**: Ensure regular database backups are configured 