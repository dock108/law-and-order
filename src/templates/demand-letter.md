# Demand Letter

**Date:** {{currentDate}}

**To:** {{insuranceCompany}}
**Adjuster:** [Insurance Adjuster Name/Claims Department]
**Address:** [Insurance Company Address]

**From:** [Your Law Firm Name/Your Name]
**Address:** [Your Law Firm Address]
**Phone:** [Your Phone]
**Email:** [Your Email]

**Re: Claim for {{clientName}}**
**Date of Incident:** {{incidentDateFormatted}}
**Location of Incident:** {{location}}
**Claim Number (if known):** [Insurance Claim Number]

Dear Claims Adjuster,

Please be advised that this office represents **{{clientName}}** in connection with the injuries and damages sustained as a result of an incident that occurred on **{{incidentDateFormatted}}** at approximately [Time of Incident] at **{{location}}**.

**Facts of the Incident:**
[Provide a brief, factual description of how the incident occurred, clearly establishing liability of the insured party. Example: Our client was lawfully proceeding through the intersection when your insured failed to yield the right-of-way and collided with our client's vehicle.]

**Injuries Sustained:**
As a direct result of this incident, {{clientName}} sustained significant injuries, including but not limited to:

{{#if injuryDetails}}
* {{injuryDetails}}
{{else}}
* [Detailed list of injuries based on medical records - to be filled in]
{{/if}}

These injuries have required extensive medical treatment and have resulted in considerable pain and suffering.

**Damages:**
We are currently compiling all medical bills, records, and documentation related to the damages sustained by {{clientName}}. These damages include, but are not limited to:

* Medical Expenses: {{#if medicalExpensesFormatted}}${{medicalExpensesFormatted}}{{else}}[Amount, e.g., $5,000.00 - update as known]{{/if}} (to date)
* Lost Wages: [Amount, if applicable]
* Pain and Suffering: [To be determined]
* Property Damage: [Amount, if applicable]

We demand full compensation for all damages incurred by our client as a result of the negligence of your insured.

Please direct all future correspondence regarding this matter to our office. We request that you acknowledge receipt of this letter within fifteen (15) days and provide the applicable policy limits for your insured.

We look forward to your prompt response and cooperation in resolving this claim amicably. Please preserve all evidence related to this incident, including any surveillance footage, photographs, and witness statements.

Sincerely,

[Your Name/Law Firm Name] 