# Document Templates Guide

This guide explains how to create and use document templates in the Law & Order application.

## Template Structure

Templates are stored in the `src/templates` directory as Markdown (`.md`) files. They use Handlebars syntax for variable interpolation, allowing dynamic content to be inserted based on client data.

## Creating a New Template

### Basic Template Structure

1. Create a new Markdown file in the `src/templates` directory (e.g., `my-template.md`)
2. Use Handlebars syntax (`{{variableName}}`) to insert dynamic content
3. Use Markdown formatting for the document structure

Here's a simple example:

```markdown
# {{documentType}} for {{clientName}}

Date: {{currentDate}}

Dear {{clientName}},

This letter serves as formal notification that our law firm will be representing you in connection with the incident that occurred on {{incidentDateFormatted}}.

Sincerely,
Law & Order Legal Firm
```

### Available Variables

The following client data variables are available in templates:

- `{{clientName}}` - Client's full name
- `{{email}}` - Client's email address
- `{{phone}}` - Client's phone number
- `{{incidentDate}}` - Date of the incident (raw)
- `{{incidentDateFormatted}}` - Formatted date of the incident
- `{{location}}` - Location of the incident
- `{{injuryDetails}}` - Details of the client's injuries
- `{{medicalExpenses}}` - Medical expenses (raw number)
- `{{medicalExpensesFormatted}}` - Formatted medical expenses as currency
- `{{insuranceCompany}}` - Name of the insurance company
- `{{lawyerNotes}}` - Lawyer's notes about the case
- `{{currentDate}}` - The current date (formatted)

You can also access any field from the client data using its exact field name.

### Formatting in Templates

You can use all standard Markdown formatting in your templates:

- **Headings**: Use `#` for headings (e.g., `# Heading 1`, `## Heading 2`)
- **Emphasis**: Use `*italic*` or `_italic_` for italics, `**bold**` or `__bold__` for bold
- **Lists**:
  - Bullet points: `- Item` or `* Item`
  - Numbered lists: `1. Item`
- **Horizontal lines**: Use `---` for horizontal lines
- **Blockquotes**: Use `>` for blockquotes
- **Links**: Use `[text](url)` for links
- **Tables**: Use Markdown table syntax

When documents are converted to PDF, the Markdown formatting is properly processed to create a well-formatted document.

## Using Templates

### Automatic Document Generation

When a new client is added, the system automatically generates documents based on the templates defined in `DEFAULT_ONBOARDING_TEMPLATES` in `src/app/api/clients/route.ts`. By default, this includes:

- `demand-letter.md`
- `representation-letter.md`

To change which templates are automatically generated, modify the `DEFAULT_ONBOARDING_TEMPLATES` array.

### Manual Document Generation

Users can also manually generate documents from templates for existing clients:

1. Navigate to the client's detail page
2. Use the "Generate Document" feature
3. Select the template to use

### Customizing Document Processing

For advanced customization of how Markdown is processed for PDF generation, you can modify the `processMarkdownForPDF` function in `src/lib/templates.ts`.

## Example Templates

### Demand Letter

```markdown
# DEMAND LETTER

{{currentDate}}

{{insuranceCompany}}
[Insurance Company Address]

Re: Our Client: {{clientName}}
    Date of Loss: {{incidentDateFormatted}}
    Claim Number: [Claim Number]

Dear Claims Representative:

Please be advised that our firm represents {{clientName}} in connection with injuries sustained in an incident on {{incidentDateFormatted}}.

## INCIDENT DETAILS

On {{incidentDateFormatted}}, our client was involved in an incident at {{location}}. {{injuryDetails}}

## DAMAGES

As a result of this incident, our client has incurred medical expenses totaling {{medicalExpensesFormatted}} to date. These expenses include:

- Emergency room treatment
- Follow-up medical appointments
- Physical therapy
- Prescription medications

## DEMAND

Based on the circumstances of this case, including liability, damages, and our client's pain and suffering, we hereby demand {{medicalExpensesFormatted}} to resolve this matter.

Please respond to this demand within 30 days. If we do not hear from you, we will assume you have rejected our demand and will proceed accordingly.

Sincerely,

Law & Order Legal Firm
```

### Representation Letter

```markdown
# REPRESENTATION LETTER

{{currentDate}}

Dear {{clientName}},

This letter confirms that you have retained Law & Order Legal Firm to represent you in connection with injuries sustained on {{incidentDateFormatted}} at {{location}}.

## SCOPE OF REPRESENTATION

We will:
1. Investigate the circumstances of your incident
2. Gather and analyze evidence
3. Communicate with insurance companies and other parties
4. Negotiate a settlement when appropriate
5. File a lawsuit if necessary

## FEE ARRANGEMENT

Our firm works on a contingency fee basis. This means we will receive 33.33% of any recovery obtained before filing a lawsuit, or 40% if a lawsuit is filed.

## CLIENT RESPONSIBILITIES

You agree to:
1. Provide accurate information
2. Attend medical appointments
3. Keep us informed of any changes in your contact information
4. Not communicate directly with insurance companies without our knowledge

Please sign below to indicate your agreement to these terms.

Sincerely,

Law & Order Legal Firm

____________________________
{{clientName}}, Client

____________________________
Date
```

## Advanced Templating

For more advanced templates, you can:

1. Use Handlebars conditional logic (`{{#if}}...{{/if}}`)
2. Create loops with `{{#each}}...{{/each}}`
3. Use Handlebars helpers for formatting
4. Create nested content structures
5. Include Partials if repeatable components are needed

Consult the [Handlebars documentation](https://handlebarsjs.com/guide/) for more advanced templating features. 