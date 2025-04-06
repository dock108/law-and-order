# Lawyer Document Automation MVP  
*(Templates + AI Modifier + Document Storage)*  

**Purpose:**  
A streamlined, single-lawyer web app deployed to Vercel, leveraging existing document templates for client onboarding, automated document generation, and AI-assisted modifications. Generated documents are persistently stored and linked within each client's profile for easy access and reuse.

---

## 1. MVP Workflow Overview
- **Secure login:** Single-user attorney login.
- **Dashboard:** List existing clients; add new clients.
- **Client Intake:** Fill in client details via a form.
- **Auto-generate documents:** Populate existing document templates.
- **AI Modifier:** Allow targeted, AI-powered edits to existing documents.
- **Persistent Document Storage:** Store and link generated documents under each client's profile.
- **PDF Export/Email:** Allow documents to be downloaded or sent via email.

---

## 2. Features and Functionality

### Authentication & Dashboard
- Secure login via NextAuth.js.
- Dashboard with:
  - Client list & date of onboarding.
  - Quick link to add new clients.

### Client Intake Form
Collect essential client/case info:
- Name, email, phone number.
- Incident details (date, location, injury).
- Medical expenses, insurance details.
- Lawyer notes (optional).

### Template-based Document Generation
- Pre-defined templates stored (`.md` or `.docx` files).
- Populate client data placeholders automatically upon intake completion.
- Automatically generate documents such as:
  - Demand Letter
  - Client Representation Letter
  - Fee Agreement
  - HIPAA Authorization Form

### AI Document Modifier Utility
- Users upload existing documents to the modifier tool.
- Enter targeted instructions for AI-based document improvements (clarity, tone, additional details).
- Preview and confirm modifications before finalizing.

### Persistent Document Storage
- Generated documents stored under each client's unique record.
- Documents remain accessible in dashboard via client's profile.
- Simple links or buttons for preview, modification, download, or email resend.

### PDF Export & Email Functionality
- Generate PDF via serverless functions (jsPDF/Puppeteer).
- Allow direct download from dashboard or email directly to client.

---

## 3. Database Schema (Enhanced for Document Storage)

TRIPLETICKsql
Clients (
  client_id UUID PRIMARY KEY,
  name TEXT,
  email TEXT,
  phone TEXT,
  incident_date DATE,
  location TEXT,
  injury_details TEXT,
  medical_expenses DECIMAL(10,2),
  insurance_company TEXT,
  lawyer_notes TEXT,
  onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

Documents (
  document_id UUID PRIMARY KEY,
  client_id UUID REFERENCES Clients(client_id),
  document_type TEXT, -- e.g., Demand Letter, Representation Letter
  file_url TEXT, -- path or link to stored PDF
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
TRIPLETICK

---

## 4. Document Modifier AI Prompts

Example Prompts for Modifier Tool:

- **Adjust Document Tone:**
  TRIPLETICK
  "Make the following document's tone more assertive and clearly emphasize liability for injuries sustained by the client."
  TRIPLETICK

- **Specific Detail Enhancement:**
  TRIPLETICK
  "Clarify and expand upon the client's medical injury details, emphasizing severity and required ongoing treatments."
  TRIPLETICK

- **Simplify Legal Language:**
  TRIPLETICK
  "Rewrite this document using simpler language for client readability and comprehension, avoiding unnecessary legal jargon."
  TRIPLETICK

---

## 5. Tech Stack (Simple & Vercel-Friendly)
- **Frontend/UI:** Next.js (React)
- **Backend/API:** Next.js API Routes (Serverless)
- **Auth:** NextAuth.js
- **Database:** SQLite (local file) or Supabase/Postgres (cloud)
- **Document Processing:**
  - Template handling: Handlebars or Mustache
  - AI Modifier: OpenAI ChatGPT API
  - PDF Generation: jsPDF/Puppeteer
- **Storage (Documents/PDFs):** Supabase Storage, AWS S3, or Vercel Blob Storage
- **Email:** Resend or SendGrid (simple setup)

---

## 6. Simple UI Flow
- Login → Dashboard (View Clients/Add Client) → Intake Form  
→ Documents auto-generated → Stored in client profile → Optionally Modify (AI) → Preview/export/email

---

## 7. Deployment Plan (Rapid Setup)
1. Scaffold Next.js app (`npx create-next-app`).
2. Integrate NextAuth.js for auth.
3. Create API routes for:
   - CRUD client actions
   - Template doc generation
   - Document modifications via ChatGPT API
   - PDF creation & optional email sending
4. Set up database/storage solutions.
5. Deploy on Vercel (Free or Pro tier).
6. Configure environment vars securely.

---

## 8. MVP Security & Compliance
- Limit client-sensitive data exposure in API calls to ChatGPT.
- Minimal but clear audit logging (document modifications, timestamps, instructions).
- Secure document storage, accessible only by authenticated lawyer.

---

## 9. Post-MVP Future Ideas
- Multi-user/team capability.
- Expanded audit trails for compliance.
- Integration with external systems (case management, medical records).

---

This approach ensures immediate productivity and value, storing generated documents under client profiles for quick access and easy modifications, making it straightforward, efficient, and deployable in hours rather than days.