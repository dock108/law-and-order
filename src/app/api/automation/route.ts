import { generateAndStorePdf } from '@/lib/documents';
import { NextResponse, NextRequest } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { PrismaClient, Prisma } from '@prisma/client';
import { z } from 'zod';
import { generateDocumentFromTemplate, prepareTemplateData } from '@/lib/templates';
import OpenAI from 'openai';

// --- Import Resend ---
import { Resend } from 'resend';

// --- Initialize Clients ---
const prisma = new PrismaClient();

// Initialize OpenAI (assuming key is set as checked before)
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Initialize Resend conditionally
let resend: Resend | null = null;
if (process.env.RESEND_API_KEY) {
    resend = new Resend(process.env.RESEND_API_KEY);
    console.log("Resend client initialized.");
} else {
    console.warn("RESEND_API_KEY not set. Email sending disabled, will use mailto links.");
}

const EMAIL_FROM_ADDRESS = process.env.EMAIL_FROM_ADDRESS || 'noreply@example.com';
console.log(`Using email from address: ${EMAIL_FROM_ADDRESS}`);

// Zod schema (remains the same)
const automationRequestSchema = z.object({
    taskId: z.string().uuid('Invalid Task ID format'),
    clientId: z.string().uuid('Invalid Client ID format'),
    automationType: z.enum(['EMAIL_DRAFT', 'CHATGPT_SUGGESTION', 'DOC_GENERATION', 'INITIAL_CONSULT']),
    automationConfig: z.string().optional().nullable(),
    requiresDocs: z.boolean().optional().nullable(),
});

// Define a type for the payload for better type safety
interface AutomationResponsePayload {
    success: boolean;
    message: string;
    action: string; 
    draft?: { to: string; subject: string; body: string };
    suggestions?: string[];
    mailtoLink?: string;
    documentInfo?: { status: string; template: string; filePath?: string; documentId?: string };
    generatedMarkdown?: string;
}

// --- OpenAI Helper Functions (Refined Prompts) ---

async function getConsultSuggestions(clientContext: string): Promise<string[]> {
    console.log("Calling OpenAI for consult suggestions with context:", clientContext);
    const prompt = `You are an assistant for a personal injury law firm in New Jersey.\nGiven the client context: "${clientContext}"\n\nList essential questions for the initial consultation and include a standard brief disclaimer about the consultation not forming an attorney-client relationship.\nFormat as a bulleted list (using '-').\n\nDisclaimer: AI-generated information for internal use only. Does not constitute legal advice. Verify all information.`;
    try {
        // TODO: Log the prompt being sent to OpenAI
        console.log("PROMPT (Consult Suggestions):", prompt);
        const response = await openai.chat.completions.create({ model: "gpt-4-turbo-preview", messages: [{ role: "user", content: prompt }], temperature: 0.3, max_tokens: 250 });
        const content = response.choices[0]?.message?.content;
        if (!content) throw new Error('OpenAI returned no content.');
        // TODO: Log the raw response from OpenAI
        const suggestions = content.split('\n').map(line => line.trim().replace(/^- /, '')).filter(line => line.length > 0);
        console.log("OpenAI Consult Suggestions Received:", suggestions);
        return suggestions;
    } catch (error: unknown) {
        console.error("OpenAI Consult Suggestions Error:", error);
        throw error;
    }
}

async function getLegalResearchSuggestions(caseType: string | null, incidentDetails: string | null, jurisdiction: string = "NJ"): Promise<string[]> {
    console.log(`Calling OpenAI for legal research for case type: ${caseType || 'Unknown'} in ${jurisdiction}`);
    const safeCaseType = caseType || 'general personal injury';
    const prompt = `You are a legal research assistant for a law firm in ${jurisdiction}.\nCase Type: "${safeCaseType}".\nIncident Details: "${incidentDetails || 'Not specified'}\"\n\nProvide a concise overview of key legal points for this case in ${jurisdiction}. Include sections (use ### markdown headings) for:\n1.  Potential Statutes of Limitations\n2.  Relevant Negligence Standards (e.g., comparative/contributory)\n3.  Key Statutes or Case Law Precedents (cite if possible)\n4.  Potential Damage Considerations (including caps if applicable)\n\nDisclaimer: AI-generated research outline for internal review only. Does not constitute legal advice. Verify all statutes, case law, and deadlines independently.`;
    try {
        // TODO: Log the prompt being sent to OpenAI
        console.log("PROMPT (Legal Research):", prompt);
        const response = await openai.chat.completions.create({ model: "gpt-4-turbo-preview", messages: [{ role: "user", content: prompt }], temperature: 0.3, max_tokens: 400 }); // Increased tokens slightly
        const content = response.choices[0]?.message?.content;
        if (!content) throw new Error('OpenAI returned no content.');
        // TODO: Log the raw response from OpenAI
        // Simple parsing, frontend can handle markdown H3s if needed
        const suggestions = content.split('\n').map(line => line.trim()).filter(line => line.length > 0);
        console.log("OpenAI Legal Research Suggestions Received (raw):", content);
        return suggestions;
    } catch (error: unknown) {
        console.error("OpenAI Legal Research Error:", error);
        throw error;
    }
}

async function getWitnessInterviewQuestions(caseType: string | null, incidentDetails: string | null): Promise<string[]> {
    console.log(`Calling OpenAI for witness interview questions for case type: ${caseType}`);
    const prompt = `You are an assistant for a personal injury law firm in New Jersey.\nCase Type: "${caseType || 'an incident'}".\nIncident Details: "${incidentDetails || 'limited details available'}\"\n\nGenerate a list of key questions to ask a potential witness. Focus on perspective, observations, conditions, actions, conversations, other witnesses.\nFormat as a bulleted list (using '-').\n\nDisclaimer: AI-generated suggestions for internal use only. Adapt questions based on the actual interview flow.`;
    try {
        // TODO: Log the prompt being sent to OpenAI
        console.log("PROMPT (Witness Questions):", prompt);
        const response = await openai.chat.completions.create({ model: "gpt-4-turbo-preview", messages: [{ role: "user", content: prompt }], temperature: 0.4, max_tokens: 300 });
        const content = response.choices[0]?.message?.content;
        if (!content) throw new Error('OpenAI returned no content.');
        // TODO: Log the raw response from OpenAI
        const questions = content.split('\n').map(line => line.trim().replace(/^- /, '')).filter(line => line.length > 0);
        console.log("OpenAI Witness Interview Questions Received:", questions);
        return questions;
    } catch (error: unknown) {
        console.error("OpenAI Witness Questions Error:", error);
        throw error;
    }
}

async function getEvidenceChecklist(caseType: string | null, incidentDetails?: string | null): Promise<string[]> {
    console.log(`Calling OpenAI for evidence checklist for case type: ${caseType}`);
    const safeCaseType = caseType || 'general personal injury';
    const prompt = `You are an assistant for a personal injury law firm in New Jersey.\nCase Type: "${safeCaseType}".\nIncident Details: "${incidentDetails || 'Not specified'}\"\n\nGenerate a checklist of standard evidence items (police reports, photos/videos, witness statements, medical records, bills, lost wages, etc.). Tailor slightly to case type.\nFormat as a bulleted list (using '-').\n\nDisclaimer: AI-generated list for internal planning. Ensure all relevant evidence is collected based on specific case facts.`;
    try {
        // TODO: Log the prompt being sent to OpenAI
        console.log("PROMPT (Evidence Checklist):", prompt);
        const response = await openai.chat.completions.create({ model: "gpt-4-turbo-preview", messages: [{ role: "user", content: prompt }], temperature: 0.3, max_tokens: 250 });
        const content = response.choices[0]?.message?.content;
        if (!content) throw new Error('OpenAI returned no content.');
        // TODO: Log the raw response from OpenAI
        const checklist = content.split('\n').map(line => line.trim().replace(/^- /, '')).filter(line => line.length > 0);
        console.log("OpenAI Evidence Checklist Received:", checklist);
        return checklist;
    } catch (error: unknown) {
        console.error("OpenAI Evidence Checklist Error:", error);
        throw error;
    }
}
// --- End OpenAI Helper Functions ---

// --- Main POST Handler ---
export async function POST(request: NextRequest) {
    console.log("Received POST request on /api/automation");

    const session = await getServerSession();
    if (!session) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        // --- Start: Validate Request Body --- 
        const body = await request.json();
        const validatedData = automationRequestSchema.parse(body); // Assign here
        console.log("Request body validated successfully.");
        // --- End: Validate Request Body --- 

        // --- Start: Main Logic (Moved Inside Try Block) --- 
        const { taskId, clientId, automationType, automationConfig } = validatedData; // Now definitely defined

        // Fetch Task and Client data
        const [task, client] = await Promise.all([
            prisma.task.findUnique({ where: { id: taskId }, select: { id: true, clientId: true, automationType: true, description: true, notes: true } }),
            prisma.client.findUnique({ where: { id: clientId }, select: { id: true, name: true, email: true, incidentDate: true, caseType: true, injuryDetails: true } })
        ]);

        // Validation Checks
        if (!task) return NextResponse.json({ error: 'Task not found' }, { status: 404 });
        if (!client) return NextResponse.json({ error: 'Client not found' }, { status: 404 });
        if (task.clientId !== clientId) return NextResponse.json({ error: 'Task does not belong to the specified client' }, { status: 403 });
        if (task.automationType !== automationType) return NextResponse.json({ error: 'Mismatched automation type for the task' }, { status: 400 });

        console.log(`Processing automation: ${automationType} for task ${taskId}...`);
        // Use const and the defined interface
        const responsePayload: AutomationResponsePayload = { success: true, message: 'Automation processed.', action: automationType };
        // Specify Prisma Promise type for the array
        const dbUpdates: Prisma.PrismaPromise<unknown>[] = []; 

        // Inner try-catch for automation-specific logic errors
        try {
            switch (automationType) {
                case 'INITIAL_CONSULT':
                    {
                        // ... (existing logic to determine templateName, subject, call AI etc.) ...
                        let templateName = 'initial-consult-email';
                        let suggestions: string[] = [];
                        let subject = `Initial Consultation Request - ${client.name}`;
                        // Use const for context
                        const context = `Case Type: ${client.caseType}, Injury Details: ${client.injuryDetails ? client.injuryDetails.substring(0, 100) + '...' : 'N/A'}`;
                        responsePayload.message = 'Initial consult email drafted and suggestions generated.';

                        if (automationConfig === 'witness_interview_prep') {
                            templateName = 'interview-witness';
                            subject = `Witness Interview Request - ${client.name} Case`;
                            suggestions = await getWitnessInterviewQuestions(client.caseType, client.injuryDetails);
                            responsePayload.message = 'Witness interview email drafted and questions generated.';
                            
                            // --- Update Task Notes for Witness Prep ---
                            const notesUpdate = `--- AI Suggested Witness Questions --- \n${suggestions.join('\n')}`;
                            const existingTaskNotes = await prisma.task.findUnique({ where: { id: taskId }, select: { notes: true }});
                            const newNotes = existingTaskNotes?.notes ? `${existingTaskNotes.notes}\n\n${notesUpdate}` : notesUpdate;
                            dbUpdates.push(prisma.task.update({ 
                                where: { id: taskId }, 
                                data: { notes: newNotes } 
                            }));
                            console.log(`Added witness questions to task ${taskId} notes.`);
                            // --- End Task Notes Update ---
                        } else { 
                            suggestions = await getConsultSuggestions(context);
                        }

                        const templateData = prepareTemplateData(client);
                        const emailBody = await generateDocumentFromTemplate(templateName, templateData);

                        responsePayload.draft = { subject, body: emailBody, to: '[Enter Email Here]' }; 
                        responsePayload.suggestions = suggestions;
                        console.log(`INITIAL_CONSULT/WITNESS_PREP (${automationConfig || 'consult'}) automation successful.`);

                        // Add status update for this path if desired
                        dbUpdates.push(prisma.task.update({
                            where: { id: taskId },
                            data: { status: 'Completed' } // Mark as completed once draft/suggestions are ready
                        }));
                        break;
                    }

                case 'EMAIL_DRAFT':
                    {
                        console.log(`Handling EMAIL_DRAFT with config: ${automationConfig}`);
                        let subject = `Regarding Task: ${task.description}`;
                        let bodyText = `Placeholder email for ${task.description}.\nClient: ${client.name} (${client.email})`; // Start with plain text
                        let logMessage = 'Generic email draft created.';
                        let taskUpdateStatus = 'In Progress'; // Default status update

                        // --- Generate specific content based on config ---
                        if (automationConfig === 'client_follow_up') {
                            subject = `Following Up: ${client.name} - ${client.caseType || 'Your Case'}`;
                            bodyText = `Dear ${client.name},\n\nThis is a friendly follow-up regarding your case.\n\nCould you please provide an update on [Specify information needed - e.g., your recent doctor's appointment, status of requested documents]?\n\nLet us know if you have any questions.\n\nSincerely,\n[Your Law Firm Name]`;
                            logMessage = `Client follow-up email ${resend ? 'sent' : 'drafted (mailto)'}.`;
                            taskUpdateStatus = resend ? 'Completed' : 'Awaiting User Action';
                        } else if (automationConfig === 'insurance_contact') {
                            subject = `Insurance Claim Follow Up: ${client.name} - Incident ${client.incidentDate ? client.incidentDate.toLocaleDateString() : 'N/A'}`;
                            bodyText = `To Whom It May Concern,\n\nPlease provide an update on the status of the claim for our client, ${client.name}, regarding the incident on ${client.incidentDate ? client.incidentDate.toLocaleDateString() : '[Date Missing]'}.\n\nClient Name: ${client.name}\nDate of Incident: ${client.incidentDate ? client.incidentDate.toLocaleDateString() : '[Date Missing]'}\n[Reference Number if available]\n\nThank you,\n[Your Law Firm Name]`;
                            logMessage = `Insurance contact email ${resend ? 'sent' : 'drafted (mailto)'}.`;
                            taskUpdateStatus = resend ? 'Completed' : 'Awaiting User Action';
                        } else {
                            // Generic draft message
                            logMessage = `Generic email ${resend ? 'sent' : 'drafted (mailto)'}.`;
                            taskUpdateStatus = resend ? 'Completed' : 'Awaiting User Action';
                        }
                        // --- End content generation ---

                        // --- Prepare draft object for response ---
                        responsePayload.draft = { 
                            subject: subject, 
                            body: bodyText, 
                            to: client.email || '[Client Email Missing]' // Use client email or placeholder
                        };
                        // --- End prepare draft object ---

                        if (!client.email) {
                            // Keep this check, but draft is already prepared
                            // Maybe adjust message if email is missing?
                            // For now, we let it proceed to show draft without 'To'
                            console.warn("Client email missing, draft prepared without recipient.");
                            // throw new Error('Client does not have an email address.'); // Don't throw if we just want the draft
                        }

                        // --- Attempt to Send or create Mailto ---
                        if (resend) {
                            // --- Send via Resend ---
                            console.log(`Attempting to send email via Resend to ${client.email}`);
                            // Remove unused finalHtml variable
                            // const finalHtml = wrapWithHtmlLetterhead(bodyText);

                            /*
                            // Temporarily disabled sending to only show draft
                            const sendResponse = await resend.emails.send({
                                from: EMAIL_FROM_ADDRESS,
                                to: client.email,
                                subject: subject,
                                // html: finalHtml, // Use bodyText or generate proper HTML if enabling
                                html: wrapWithHtmlLetterhead(bodyText) // Or keep using the wrapper if needed elsewhere
                            });
                            // ... rest of commented out block ...
                            */
                            responsePayload.message = 'Email draft generated and ready for review (sending disabled).'; // Update message

                            // Status update handled below
                        } else {
                            // --- Generate Mailto Link ---
                            console.log("Resend not configured. Generating mailto link.");
                            const mailtoSubject = encodeURIComponent(subject);
                            const mailtoBody = encodeURIComponent(bodyText); // Use plain text for mailto
                            const mailtoLink = `mailto:${client.email}?subject=${mailtoSubject}&body=${mailtoBody}`;
                            responsePayload.message = 'Email draft ready. Click link to open in your mail client.';
                            responsePayload.mailtoLink = mailtoLink;
                            // Status update handled below
                        }
                        // --- End Send/Mailto Logic ---

                        // --- Log Communication & Update Status ---
                        const finalLogMessage = `[${new Date().toISOString()}] ${logMessage}`;
                        const newNotes = task.notes ? `${task.notes}\n${finalLogMessage}` : finalLogMessage;
                        dbUpdates.push(prisma.task.update({
                            where: { id: taskId },
                            data: { 
                                notes: newNotes, 
                                status: taskUpdateStatus 
                            },
                        }));
                        console.log(`Logged communication and set task ${taskId} status to ${taskUpdateStatus}.`);
                        // --- End Log & Status Update ---
                        break;
                    }

                case 'CHATGPT_SUGGESTION':
                    {
                        console.log(`Handling CHATGPT_SUGGESTION with config: ${automationConfig}`);
                        let suggestions: string[] = [];
                        if (automationConfig === 'legal_research') {
                            suggestions = await getLegalResearchSuggestions(client.caseType, client.injuryDetails);
                            responsePayload.message = 'Legal research suggestions generated.';
                        } else if (automationConfig === 'case_law_research') {
                            const clientContext = `Case Type: ${client.caseType}, Injury: ${client.injuryDetails ? client.injuryDetails.substring(0,50) : 'N/A'}`;
                            suggestions = await getConsultSuggestions(clientContext);
                            responsePayload.message = 'Similar case suggestions generated.';
                        } else if (automationConfig === 'evidence_checklist') {
                            suggestions = await getEvidenceChecklist(client.caseType, client.injuryDetails);
                            responsePayload.message = 'Evidence checklist generated.';
                        } else {
                            // Generic suggestion using OpenAI (with disclaimer now included in prompt)
                            const genericPrompt = `Provide a brief, generic suggestion for how to approach the task: "${task.description}" for a client named ${client.name}.\nDisclaimer: AI-generated suggestion for internal consideration only.`;
                            // TODO: Log the prompt being sent to OpenAI
                            console.log("PROMPT (Generic Suggestion):", genericPrompt);
                            const genericResponse = await openai.chat.completions.create({ model: "gpt-3.5-turbo", messages: [{ role: "user", content: genericPrompt }], max_tokens: 80 });
                            // TODO: Log the raw response from OpenAI
                            suggestions = genericResponse.choices[0]?.message?.content?.split('\n').filter(l => l.length > 0) || ['Review client file and proceed.'];
                            responsePayload.message = 'Generic suggestion generated.';
                        }
                        responsePayload.suggestions = suggestions;

                        // --- Update Task Status ---
                        dbUpdates.push(prisma.task.update({
                            where: { id: taskId },
                            data: { status: 'Completed' } // Mark task complete after generating suggestions
                        }));
                        // --- End Task Status Update ---

                        // --- TODO: Optionally save suggestions to Task Notes ---
                        /*
                        const notesUpdate = `--- AI Suggestions (${automationConfig || 'Generic'}) --- \n${suggestions.join('\n')}`;
                        const existingTaskNotes = await prisma.task.findUnique({ where: { id: taskId }, select: { notes: true }});
                        const newNotes = existingTaskNotes?.notes ? `${existingTaskNotes.notes}\n\n${notesUpdate}` : notesUpdate;
                        dbUpdates.push(prisma.task.update({
                            where: { id: taskId },
                            data: { notes: newNotes }
                        }));
                        */
                        // --- End Save Notes ---

                        console.log('CHATGPT_SUGGESTION automation successful.');
                        break;
                    }

                case 'DOC_GENERATION':
                    {
                        const templateName = automationConfig; 
                        if (!templateName) {
                            throw new Error('Document generation requires an automationConfig specifying the template name.');
                        }
                        console.log(`Generating document: ${templateName} for client ${client.id}`);
                        const templateData = prepareTemplateData(client);
                        const generatedContent = await generateDocumentFromTemplate(templateName, templateData);
                        const pdfResult = await generateAndStorePdf({
                            markdownContent: generatedContent,
                            clientId: client.id,
                            documentType: templateName,
                        });

                        // --- Update Task Status ---
                        dbUpdates.push(prisma.task.update({
                            where: { id: taskId },
                            data: { status: 'Completed' }, // Mark as completed
                        }));
                        console.log(`Task ${taskId} status updated to Completed after doc generation.`);
                        // --- End Task Status Update ---

                        responsePayload.message = `Document '${templateName}' generated successfully.`;
                        responsePayload.generatedMarkdown = generatedContent;
                        responsePayload.documentInfo = {
                            status: 'Generated',
                            template: templateName,
                            filePath: pdfResult.filePath,
                            documentId: pdfResult.documentId,
                        };
                        console.log('DOC_GENERATION automation successful for template:', templateName);
                        break;
                    }

                default:
                    console.error(`Unhandled automation type: ${automationType}`);
                    throw new Error(`Invalid automation type: ${automationType}`);
            }

            // --- Execute all DB updates ---
            if (dbUpdates.length > 0) {
                await Promise.all(dbUpdates);
                console.log("Database updates completed successfully.");
            }
            // --- End DB Updates ---

        } catch (automationError: unknown) { // Use unknown for catch block error
            // ... (existing error handling for automation logic)
            console.error(`Error during ${automationType} automation execution:`, automationError);
            const message = automationError instanceof Error ? automationError.message : 'Unknown automation error';
            return NextResponse.json({ error: `Failed to process automation: ${message}` }, { status: 500 });
        }

        // ... (existing success response)
        console.log("Automation processed successfully, returning payload:", responsePayload);
        return NextResponse.json(responsePayload, { status: 200 });

    } catch (error: unknown) { // Use unknown for catch block error
        // ... (existing broader error handling)
        console.error(`Error processing automation request:`, error); // Removed taskId as it might not be defined here
        const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
        return NextResponse.json({ error: `Internal server error processing automation request: ${errorMessage}` }, { status: 500 });
    }
} 