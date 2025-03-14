from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Define the detailed legal document text
document_text = """DETAILED LEGAL SERVICES AGREEMENT

This Detailed Legal Services Agreement ("Agreement") is made and entered into as of the 1st day of March, 2025 ("Effective Date") by and between:

ABC Legal Solutions, LLC, a limited liability company organized under the laws of the State of Delaware, with its principal place of business at 123 Legal Plaza, Wilmington, DE 19801 ("Service Provider"), and

John Doe, an individual residing at 456 Main Street, Anytown, USA ("Client").

1. DEFINITIONS
1.1 "Confidential Information" means all information disclosed by one party to the other, whether orally or in writing, that is designated as confidential or that reasonably should be understood to be confidential given the nature of the information and the circumstances of disclosure, including, without limitation, business strategies, financial information, client lists, and technical data.
1.2 "Services" means all legal consultation, representation, and advisory services provided by Service Provider to Client pursuant to this Agreement, as more specifically described in Exhibit A attached hereto.
1.3 "Deliverables" means any work product, reports, analyses, or documents created by Service Provider in the performance of the Services.

2. SCOPE OF SERVICES
2.1 Services Provided. Service Provider shall provide Client with legal consultation and advisory services, which may include, but are not limited to, contract review and drafting, regulatory compliance, litigation support, intellectual property rights analysis, and employment law advisory.
2.2 Modifications. The parties may mutually agree in writing to modify or expand the scope of Services. Any modifications shall be subject to the terms and conditions of this Agreement.
2.3 Exhibit A. A detailed description of the Services to be provided is set forth in Exhibit A, which is incorporated herein by reference.

3. TERM AND TERMINATION
3.1 Term. This Agreement shall commence on the Effective Date and continue for one (1) year unless terminated earlier.
3.2 Termination for Convenience. Either party may terminate this Agreement at any time without cause upon thirty (30) days’ prior written notice.
3.3 Termination for Cause. Either party may terminate this Agreement immediately if the other party breaches any material term and fails to cure such breach within fifteen (15) days.
3.4 Effect of Termination. Upon termination, Client shall pay for all Services rendered up to the effective date of termination.

4. FEES AND PAYMENT
4.1 Fee Structure. Client shall pay Service Provider an hourly fee of $300 per hour unless otherwise agreed upon.
4.2 Invoicing. Service Provider will issue invoices monthly with a detailed description of the Services provided.
4.3 Payment Terms. Payments are due within thirty (30) days of invoice receipt. Late payments may incur a service charge of 1.5% per month.
4.4 Expenses. Client agrees to reimburse Service Provider for pre-approved expenses incurred in performing the Services.

5. CONFIDENTIALITY
5.1 Each party agrees to maintain the confidentiality of the other’s Confidential Information and to use it solely for purposes of performing this Agreement.
5.2 Confidential Information excludes information that is public, received from a third party, or independently developed.
5.3 The confidentiality obligations shall survive termination for three (3) years.

6. INTELLECTUAL PROPERTY
6.1 Ownership. All Deliverables produced under this Agreement shall be considered “work made for hire” and are the sole property of Client.
6.2 License. Service Provider retains a non-exclusive license to use pre-existing intellectual property solely to perform the Services.

7. LIMITATION OF LIABILITY
7.1 In no event shall either party be liable for indirect, incidental, or consequential damages.
7.2 The total aggregate liability of either party shall not exceed the fees paid by Client in the twelve (12) months preceding the liability event.

8. INDEMNIFICATION
8.1 Service Provider shall indemnify Client for any breach of this Agreement.
8.2 Client shall indemnify Service Provider for misuse of the Deliverables or instructions provided.

9. MISCELLANEOUS
9.1 Governing Law. This Agreement is governed by the laws of the State of Delaware.
9.2 Entire Agreement. This Agreement constitutes the entire agreement between the parties.
9.3 Amendments. No amendment is valid unless in writing and signed by both parties.
9.4 Severability. If any provision is invalid, the remaining provisions shall remain in effect.
9.5 Notices. All notices must be in writing and are deemed given when delivered.
9.6 Counterparts. This Agreement may be executed in counterparts, each of which is deemed an original.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.

ABC Legal Solutions, LLC
By: _______________________________
Name: _____________________________
Title: ______________________________

John Doe
By: _______________________________
Name: John Doe
Date: ______________________________
"""

# Create a canvas and generate the PDF
pdf_filename = "detailed_legal_document.pdf"
c = canvas.Canvas(pdf_filename, pagesize=letter)
width, height = letter

# Start a text object at a margin
text_object = c.beginText(40, height - 40)
lines = document_text.splitlines()
for line in lines:
    text_object.textLine(line)
    # If the text reaches near the bottom, create a new page
    if text_object.getY() < 40:
        c.drawText(text_object)
        c.showPage()
        text_object = c.beginText(40, height - 40)

c.drawText(text_object)
c.save()

print(f"PDF generated successfully: {pdf_filename}")
