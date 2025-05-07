# SETTLEMENT DISBURSEMENT STATEMENT

## [ Smith & Associates Law Firm ]

123 Legal Street, Suite 100
New York, NY 10001
Tel: (555) 123-4567
Email: contact@smithlawfirm.com

---

## CLIENT INFORMATION

**Client Name:** {{ client.full_name }}
**Case Number:** {{ incident.id }}
**Date of Incident:** {{ incident.date }}
**Date of Settlement:** {{ today() }}

---

## SETTLEMENT CALCULATION

| Item                                                | Amount                                       |
| --------------------------------------------------- | -------------------------------------------- |
| **TOTAL SETTLEMENT**                                | ${{ "{:,.2f}".format(totals.gross) }}        |
| **Attorney Fee ({{ incident.attorney_fee_pct }}%)** | ${{ "{:,.2f}".format(totals.attorney_fee) }} |
| **Medical Liens**                                   | ${{ "{:,.2f}".format(totals.lien_total) }}   |

{% if totals.other_adjustments > 0 %}
| **Other Deductions/Adjustments** | ${{ "{:,.2f}".format(totals.other_adjustments) }} |
{% endif %}
| **NET TO CLIENT** | ${{ "{:,.2f}".format(totals.net_to_client) }} |

---

## DISBURSEMENT APPROVAL

I, {{ client.full_name }}, have reviewed this settlement disbursement statement and agree to the distribution of funds as outlined above. I understand that upon signing this document, I authorize the law firm to distribute the settlement funds according to this statement.

Signature: **\*\*\*\***\_\_\_\_**\*\*\*\***

Date: \***\*\*\*\*\***\_\_\_\_\***\*\*\*\*\***

---

## ATTORNEY CERTIFICATION

As the attorney of record, I certify that this disbursement statement accurately reflects the settlement received, fees, costs, and disbursements in this matter.

Attorney Signature: **\*\*\*\***\_\_\_\_**\*\*\*\***

Date: \***\*\*\*\*\***\_\_\_\_\***\*\*\*\*\***
