# Law & Order Documentation

Welcome to the Law & Order documentation. This directory contains information about setting up, using, and deploying the application.

## Available Documentation

- [Setup Guide](setup.md) - Instructions for setting up the project environment and dependencies
- [Templates Guide](templates.md) - How to create and use document templates
- [Markdown Processing](markdown-processing.md) - Details about Markdown processing for PDF generation
- [Deployment Guide](deployment.md) - How to deploy the application to Vercel

## Project Overview

Law & Order is a Next.js application designed for law firms to automate client onboarding, document generation, and management. It features:

- Client management
- Document generation from templates
- PDF creation and storage
- Email integration
- AI assistance for document modification

## Key Technologies

- Next.js (App Router)
- Prisma ORM
- NextAuth.js for authentication
- Supabase for storage
- jsPDF for PDF generation
- OpenAI for document modifications
- Resend for email delivery
- Handlebars for template processing
- Tailwind CSS for styling

## Quick Start

1. Set up environment variables
2. Install dependencies with `npm install`
3. Set up database with `npx prisma migrate dev --name init`
4. Create Supabase storage bucket
5. Run the development server with `npm run dev`

See the [Setup Guide](setup.md) for detailed instructions.

## Further Reading

- [Main README](../README.md) - Project overview and basic information
- [CHANGELOG](../CHANGELOG.md) - History of changes to the project
- [MVP Documentation](../mvp.md) - Original MVP specification 