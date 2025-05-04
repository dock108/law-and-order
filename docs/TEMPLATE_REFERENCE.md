# Template Reference

This document provides a reference for all the Jinja template tags used in the personal injury document templates.

## Docassemble Integration

Templates in the `templates/` directory are bind-mounted to the Docassemble container at `/usr/share/docassemble/files/templates`. This allows you to directly use these templates in your Docassemble interviews for document automation.

To use a template in a Docassemble interview:

```yaml
---
template: your_template.yml
path: /usr/share/docassemble/files/templates
```

Run the Docassemble container locally with the instructions in the [README.md](../README.md) to test your templates.

## Common Tags

### Client Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ client.full_name }}` | Client's full name | John Smith |
| `{{ client.last_name }}` | Client's last name | Smith |
| `{{ client.first_name }}` | Client's first name | John |
| `{{ client.dob }}` | Client's date of birth | 01/15/1980 |
| `{{ client.ssn }}` | Client's Social Security Number | 123-45-6789 |
| `{{ client.address }}` | Client's street address | 123 Main Street |
| `{{ client.city }}` | Client's city | New York |
| `{{ client.state }}` | Client's state | NY |
| `{{ client.zip }}` | Client's ZIP code | 10001 |
| `{{ client.phone }}` | Client's phone number | (212) 555-1234 |
| `{{ client.email }}` | Client's email address | john.smith@example.com |
| `{{ client.home_phone }}` | Client's home phone | (212) 555-9876 |
| `{{ client.cell_phone }}` | Client's cell phone | (917) 555-1234 |
| `{{ client.contact_preference }}` | Preferred contact method | Email |
| `{{ client.marital_status }}` | Marital status | Married |
| `{{ client.spouse_name }}` | Spouse's name | Jane Smith |
| `{{ client.employer }}` | Employer name | Acme Corporation |
| `{{ client.occupation }}` | Occupation | Software Developer |
| `{{ client.work_address }}` | Work address | 555 Tech Blvd |
| `{{ client.work_phone }}` | Work phone | (212) 555-5678 |
| `{{ client.monthly_income }}` | Monthly income | 7,500.00 |
| `{{ client.lost_wages }}` | Lost wages to date | 15,000.00 |
| `{{ client.surgery }}` | Whether client had surgery | True |

### Attorney/Firm Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ attorney.full_name }}` | Attorney's full name | Jane Doe |
| `{{ attorney.name }}` | Attorney's name (used in memos) | Jane Doe |
| `{{ attorney.title }}` | Attorney's title | Partner |
| `{{ firm.name }}` | Law firm name | Smith & Jones Law Firm |
| `{{ firm.address }}` | Firm's street address | 456 Park Avenue |
| `{{ firm.city }}` | Firm's city | New York |
| `{{ firm.state }}` | Firm's state | NY |
| `{{ firm.zip }}` | Firm's ZIP code | 10022 |
| `{{ firm.phone }}` | Firm's phone number | (212) 555-5678 |
| `{{ firm.fax }}` | Firm's fax number | (212) 555-5679 |
| `{{ firm.email }}` | Firm's email address | info@smithjones.com |
| `{{ firm.records_email }}` | Email for records requests | records@smithjones.com |

### Staff Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ staff.name }}` | Staff member's name | Alex Johnson |
| `{{ staff.title }}` | Staff member's title | Paralegal |
| `{{ staff.support }}` | Support staff designation | Legal Assistant |

### Incident Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ incident.date }}` | Date of incident | 06/15/2023 |
| `{{ incident.type }}` | Type of incident | Motor Vehicle Accident |
| `{{ incident.location }}` | Location of incident | Intersection of Main St. and Broadway |
| `{{ incident.description }}` | Detailed description | Client was stopped at a red light when rear-ended by defendant |

### Insurance Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ insurance.company_name }}` | Insurance company name | Acme Insurance Co. |
| `{{ insurance.adjuster_name }}` | Insurance adjuster's name | Robert Johnson |
| `{{ insurance.company_address }}` | Insurance company address | 789 Corporate Blvd. |
| `{{ insurance.company_city }}` | Insurance company city | Newark |
| `{{ insurance.company_state }}` | Insurance company state | NJ |
| `{{ insurance.company_zip }}` | Insurance company ZIP | 07102 |
| `{{ claim.number }}` | Claim number | ABC123456789 |
| `{{ policy.number }}` | Policy number | POL987654321 |

### Insured Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ insured.full_name }}` | Insured's full name | James Williams |

### Medical Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ medical.start_date }}` | Start date of medical services | 06/15/2023 |
| `{{ medical.end_date }}` | End date of medical services | 12/15/2023 |
| `{{ medical.specific_records }}` | Specific medical records requested | MRI results from 07/01/2023 |
| `{{ provider.name }}` | Medical provider name | City General Hospital |
| `{{ provider.address }}` | Provider address | 100 Hospital Drive |
| `{{ provider.city }}` | Provider city | New York |
| `{{ provider.state }}` | Provider state | NY |
| `{{ provider.zip }}` | Provider ZIP code | 10003 |

### Representative Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ representative.name }}` | Representative's name | Mary Smith |
| `{{ representative.authority }}` | Representative's authority | Power of Attorney |

### Authorization Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ authorization.expiration }}` | Expiration of authorization | One year from date of signature |

### Date Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ today.date }}` | Current date | May 5, 2024 |

### Fee Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ fee.percentage }}` | Contingency fee percentage | 33.33 |
| `{{ fee.amount }}` | Calculated fee amount | 10,000.00 |

## Specialized Tags

### Demand Letter Tags

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ liability.description }}` | Description of liability | The defendant was 100% at fault |
| `{{ injuries }}` | List of injuries | Array of injury objects |
| `{{ injury.description }}` | Description of an injury | Cervical spine strain |
| `{{ treatments }}` | List of treatments | Array of treatment objects |
| `{{ treatment.provider }}` | Treatment provider | Dr. Smith |
| `{{ treatment.dates }}` | Treatment dates | 06/20/2023 - 09/15/2023 |
| `{{ treatment.description }}` | Treatment description | Physical therapy, 3x per week |
| `{{ medical_expenses }}` | List of medical expenses | Array of expense objects |
| `{{ expense.provider }}` | Expense provider | City General Hospital |
| `{{ expense.amount }}` | Expense amount | 5,000.00 |
| `{{ medical_expenses.total }}` | Total medical expenses | 15,000.00 |
| `{{ lost_wages.start_date }}` | Start date of lost work | 06/16/2023 |
| `{{ lost_wages.end_date }}` | End date of lost work | 07/30/2023 |
| `{{ lost_wages.amount }}` | Total lost wages | 6,000.00 |
| `{{ pain_suffering.description }}` | Description of pain and suffering | Client continues to experience daily pain |
| `{{ demand.amount }}` | Settlement demand amount | 75,000.00 |
| `{{ demand.expiration_days }}` | Days until demand expires | 30 |

### Settlement Tags

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ matter.description }}` | Description of legal matter | Motor Vehicle Accident on 06/15/2023 |
| `{{ settlement.date }}` | Date of settlement | 04/20/2024 |
| `{{ settlement.gross_amount }}` | Gross settlement amount | 50,000.00 |
| `{{ settlement.net_client }}` | Net amount to client | 30,000.00 |
| `{{ case_expenses }}` | List of case expenses | Array of expense objects |
| `{{ case_expenses.total }}` | Total case expenses | 2,000.00 |
| `{{ medical_liens }}` | List of medical liens | Array of lien objects |
| `{{ medical_liens.total }}` | Total medical liens | 5,000.00 |
| `{{ other_liens }}` | List of other liens | Array of lien objects |
| `{{ other_liens.total }}` | Total other liens | 3,000.00 |
| `{{ lien.provider }}` | Lien provider | City General Hospital |
| `{{ lien.description }}` | Lien description | Medicare lien |
| `{{ lien.amount }}` | Lien amount | 3,000.00 |

### Workflow Tags

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ tasks }}` | List of tasks | Array of task objects |
| `{{ task.description }}` | Description of a task | Request medical records from City General Hospital |
| `{{ experts }}` | List of experts | Array of expert objects |
| `{{ expert.name }}` | Expert's name | Dr. Jane Smith, Orthopedic Surgeon |

### Case Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ case.reference }}` | Internal case reference number | PI-2024-123 |
| `{{ case.number }}` | Court case number | CV-2024-9876 |

### Insurance Offer Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ offer.amount }}` | Settlement offer amount | 25,000.00 |
| `{{ offer.date }}` | Date of settlement offer | April 20, 2024 |
| `{{ response.timeframe }}` | Response timeframe | 14 |
| `{{ demand.original_amount }}` | Original demand amount | 100,000.00 |
| `{{ demand.revised_amount }}` | Revised demand amount | 85,000.00 |

### Medical Balance Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ medical.balance }}` | Outstanding medical balance | 12,500.00 |

### Client Insurance Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ client_insurance.company }}` | Client's insurance company | State Farm |
| `{{ client_insurance.policy_number }}` | Client's policy number | SF123456789 |
| `{{ client_insurance.agent }}` | Client's insurance agent | Bob Johnson |
| `{{ client_insurance.phone }}` | Client's insurance phone | (800) 555-1212 |

### Other Party's Insurance Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ other_insurance.company }}` | Other party's insurance | Allstate |
| `{{ other_insurance.policy_number }}` | Other party's policy number | AL987654321 |
| `{{ other_insurance.claim_number }}` | Other party's claim number | CL-12345-A |
| `{{ other_insurance.adjuster }}` | Other party's adjuster | Sarah Williams |
| `{{ other_insurance.phone }}` | Other party's insurance phone | (888) 555-9999 |

### Witness Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ witnesses }}` | List of witnesses | Array of witness objects |
| `{{ witness.name }}` | Witness name | Robert Taylor |
| `{{ witness.phone }}` | Witness phone | (212) 555-3333 |
| `{{ witness.relationship }}` | Witness relationship to client | Friend |

### Prior Claims Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ prior_claims.has_prior }}` | Whether client has prior claims | Yes |
| `{{ prior_claims.details }}` | List of prior claims | Array of claim objects |
| `{{ claim.date }}` | Prior claim date | 05/10/2022 |
| `{{ claim.type }}` | Prior claim type | Slip and Fall |
| `{{ claim.outcome }}` | Prior claim outcome | Settled for $15,000 |

### Referral Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ referral.source }}` | Referral source | Former client |
| `{{ referral.person }}` | Referring person | Michael Johnson |

### Future Medical Costs

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ future_medical.estimated_cost }}` | Estimated future medical costs | 25,000.00 |

### Law Firm Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ firm.retention_years }}` | File retention period | 7 |

### Legal Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ jurisdiction.statute }}` | Jurisdiction statute | NY CPLR § 302 |
| `{{ venue.statute }}` | Venue statute | NY CPLR § 503 |
| `{{ defendant.name }}` | Defendant's name | John Doe |
| `{{ defendant.county }}` | Defendant's county | Kings |
| `{{ defendant.state }}` | Defendant's state | NY |
| `{{ defendant.address }}` | Defendant's address | 789 Oak Street |
| `{{ defendant.city }}` | Defendant's city | Brooklyn |
| `{{ defendant.zip }}` | Defendant's ZIP code | 11201 |
| `{{ plaintiff.full_name }}` | Plaintiff's full name (typically client) | John Smith |
| `{{ plaintiff.county }}` | Plaintiff's county | New York |
| `{{ plaintiff.state }}` | Plaintiff's state | NY |
| `{{ plaintiff.address }}` | Plaintiff's address | 123 Main Street |
| `{{ plaintiff.city }}` | Plaintiff's city | New York |
| `{{ plaintiff.zip }}` | Plaintiff's ZIP code | 10001 |
| `{{ plaintiff.activity }}` | Plaintiff's activity at time of incident | walking on the sidewalk |
| `{{ defendant.activity }}` | Defendant's activity at time of incident | operating a motor vehicle |
| `{{ negligence_allegations }}` | List of negligence allegations | Array of allegation objects |
| `{{ allegation.description }}` | Description of negligence allegation | Failing to maintain proper lookout |
| `{{ duty.description }}` | Description of duty | operating a motor vehicle |
| `{{ damages.jurisdictional_minimum }}` | Jurisdictional minimum for damages | $25,000 |
| `{{ incident.county }}` | County where incident occurred | New York |
| `{{ incident.state }}` | State where incident occurred | NY |
| `{{ incident.time }}` | Time of incident | 3:30 p.m. |
| `{{ attorney.bar_number }}` | Attorney's bar number | NY123456 |

### Settlement Release Information

| Tag | Description | Example Value |
|-----|-------------|---------------|
| `{{ settlement.gross_amount_numeric }}` | Settlement amount in numeric format | 50000.00 |
| `{{ state_venue.name }}` | State for notarization purposes | NEW YORK |
| `{{ county_venue.name }}` | County for notarization purposes | NEW YORK |
| `{{ notary.date }}` | Date of notarization | 5th day of May, 2024 |
| `{{ notary.id_type }}` | Identification type for notarization | New York Driver's License |
| `{{ notary.expiration }}` | Notary commission expiration | December 31, 2025 |

# Email Template Reference

This document describes the available email templates in the PI Auto system and the context variables that can be used with each template.

## Common Context Variables

These variables are available in all email templates:

| Variable | Description | Example |
|----------|-------------|---------|
| `current_year` | Current year (automatically added) | `2023` |
| `support_email` | Support email address | `support@example.com` |
| `support_phone` | Support phone number | `555-123-4567` |

## Templates

### `welcome.html`

Sent to new clients after they've completed the intake process.

**Additional Context Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `client.full_name` | Client's full name | `John Doe` |
| `client.email` | Client's email address | `john.doe@example.com` |

**Example Usage:**

```python
from pi_auto_api.externals.sendgrid_client import send_mail

await send_mail(
    template_name="welcome.html",
    to_email="john.doe@example.com",
    template_ctx={
        "client": {
            "full_name": "John Doe",
            "email": "john.doe@example.com"
        },
        "support_email": "support@example.com",
        "support_phone": "555-123-4567"
    }
)
```

### `retainer_sent.html`

Sent to clients after a retainer agreement has been sent via DocuSign.

**Additional Context Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `client.full_name` | Client's full name | `John Doe` |
| `client.email` | Client's email address | `john.doe@example.com` |

**Example Usage:**

```python
from pi_auto_api.externals.sendgrid_client import send_mail

await send_mail(
    template_name="retainer_sent.html",
    to_email="john.doe@example.com",
    template_ctx={
        "client": {
            "full_name": "John Doe",
            "email": "john.doe@example.com"
        },
        "support_email": "support@example.com",
        "support_phone": "555-123-4567"
    }
)
```

## Adding New Templates

To add a new email template:

1. Create a new HTML file in the `email_templates` directory.
2. Use Jinja2 syntax for template variables (e.g. `{{ client.full_name }}`).
3. Update this document with the new template and its context variables.
4. Use the `send_mail` function to send emails with the new template.

## Best Practices

1. Always include responsive design for mobile devices.
2. Keep emails simple and focused.
3. Include clear call-to-action when needed.
4. Test new templates with multiple email clients.
5. Include both HTML and plain text versions when possible.
