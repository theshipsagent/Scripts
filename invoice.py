#!/usr/bin/env python3
"""
Professional Consultancy Invoice Generator
Creates PDF invoices matching your exact template format
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


class InvoiceGenerator:
    def __init__(self):
        self.default_client = "SESCO Cement - k/a Fredrik Knutsen"
        self.default_expenses = [
            {"description": "Monthly Retainer", "amount": 8000.00},
            {"description": "Insurance Stipend", "amount": 500.00},
            {"description": "Reimbursable T&E (Attached)", "amount": 0.00},
        ]
        self.payment_info = {
            "name": "William S. Davis III",
            "address1": "1020 Forest Lakes Circle",
            "address2": "Chesapeake, VA 23322",
            "phone": "657-477-0436",
            "ach_number": "263079276",
            "account_number": "12247002"
        }

    def create_invoice(self,
                       invoice_number,
                       start_date,
                       end_date,
                       client_name=None,
                       expenses=None,
                       note="Per diem basis GSA MI&E Scale"):
        """
        Create a professional PDF invoice

        Args:
            invoice_number (str): Invoice number
            start_date (str): Start date (YYYY-MM-DD format)
            end_date (str): End date (YYYY-MM-DD format)
            client_name (str): Client name (defaults to SESCO)
            expenses (list): List of expense dicts with 'description' and 'amount'
            note (str): Note text
        """

        # Use defaults if not provided
        if client_name is None:
            client_name = self.default_client
        if expenses is None:
            expenses = self.default_expenses.copy()

        # Create filename with timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"invoice_{invoice_number}_{timestamp}.pdf"

        # Create PDF document
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.75 * inch)
        except PermissionError:
            # Try Desktop if current directory fails
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            try:
                doc = SimpleDocTemplate(desktop_path, pagesize=letter, topMargin=0.75 * inch)
                filename = desktop_path
            except PermissionError:
                # Last resort - home directory
                home_path = os.path.join(os.path.expanduser("~"), filename)
                doc = SimpleDocTemplate(home_path, pagesize=letter, topMargin=0.75 * inch)
                filename = home_path

        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        # Title
        story.append(Paragraph("Consultancy Invoice", title_style))

        # Header section with client and invoice number
        header_data = [
            [Paragraph(f"<b>To:</b> {client_name}", styles['Normal']),
             Paragraph(f"<b>Inv#</b> {invoice_number}", styles['Normal'])]
        ]
        header_table = Table(header_data, colWidths=[4.5 * inch, 2 * inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(header_table)

        # Dates section
        dates_para = Paragraph(f"<b>Dates:</b> {start_date} <b>to</b> {end_date}", styles['Normal'])
        story.append(dates_para)
        story.append(Spacer(1, 20))

        # Expense table
        table_data = [["Item", "Description of Expense", "Amount"]]

        total = 0
        for i, expense in enumerate(expenses, 1):
            amount = expense.get('amount', 0)  # Use .get() with default
            # Ensure amount is a number
            try:
                amount = float(amount) if amount else 0.0
            except (ValueError, TypeError):
                amount = 0.0

            total += amount
            # Debug: print what we're adding to table
            print(f"Adding to table: {i}. {expense['description']} = ${amount:,.2f}")
            table_data.append([
                str(i),
                expense['description'],
                f"$ {amount:,.2f}"
            ])

        # Add empty rows to match your template (up to 10 rows total)
        while len(table_data) < 11:  # 1 header + 10 data rows
            table_data.append([str(len(table_data)), "", ""])

        expense_table = Table(table_data, colWidths=[0.6 * inch, 4.4 * inch, 1.5 * inch])
        expense_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Description column left-aligned
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Amount column right-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(expense_table)

        # Note section
        story.append(Spacer(1, 15))
        note_para = Paragraph(f"<b>Note:</b> {note}", styles['Normal'])
        story.append(note_para)

        # Total section
        story.append(Spacer(1, 15))
        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
            spaceAfter=20
        )
        total_para = Paragraph(f"$ {total:,.2f}", total_style)
        story.append(total_para)

        # Payment information footer
        story.append(Spacer(1, 30))

        # Create separate paragraphs for payment info
        payment_left = f"""<b>ACH Payment:</b><br/>
{self.payment_info['name']}<br/>
{self.payment_info['address1']}<br/>
{self.payment_info['address2']}<br/>
<b>Tel:</b> {self.payment_info['phone']}"""

        payment_right = f"""<b>ACH#</b> {self.payment_info['ach_number']}<br/>
<b>Acct#</b> {self.payment_info['account_number']}"""

        payment_data = [
            [Paragraph(payment_left, styles['Normal']),
             Paragraph(payment_right, styles['Normal'])]
        ]
        payment_table = Table(payment_data, colWidths=[4 * inch, 2.5 * inch])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(payment_table)

        # Build PDF
        doc.build(story)
        return filename, total


def main():
    """Example usage and interactive invoice creator"""

    generator = InvoiceGenerator()

    print("🧾 Professional Invoice Generator")
    print("=" * 40)

    # Get invoice details
    invoice_num = input("Invoice Number: ").strip()
    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    end_date = input("End Date (YYYY-MM-DD): ").strip()

    # Use default client or custom
    use_default_client = input(f"Use default client ({generator.default_client})? (y/n): ").lower().startswith('y')
    client_name = None if use_default_client else input("Client Name: ").strip()

    # Start with default expenses
    expenses = generator.default_expenses.copy()
    print(f"\nDefault expenses loaded:")
    for i, exp in enumerate(expenses, 1):
        print(f"  {i}. {exp['description']}: ${exp['amount']:,.2f}")

    # Option to modify T&E amount
    modify_te = input("\nModify Reimbursable T&E amount? (y/n): ").lower().startswith('y')
    if modify_te:
        try:
            te_input = input("New T&E amount: $").strip()
            new_amount = float(te_input)
            expenses[2]['amount'] = new_amount
            print(f"✅ T&E amount set to: ${new_amount:,.2f}")
        except ValueError:
            print(f"❌ Invalid amount '{te_input}', keeping $0.00")
            expenses[2]['amount'] = 0.00

    # Option to add more expenses
    add_more = input("Add additional expenses? (y/n): ").lower().startswith('y')
    if add_more:
        while True:
            desc = input("Expense description (or 'done'): ").strip()
            if desc.lower() == 'done':
                break
            try:
                amount = float(input("Amount: $"))
                expenses.append({"description": desc, "amount": amount})
            except ValueError:
                print("Invalid amount, skipping this expense")

    # Generate invoice
    try:
        filename, total = generator.create_invoice(
            invoice_number=invoice_num,
            start_date=start_date,
            end_date=end_date,
            client_name=client_name,
            expenses=expenses
        )

        print(f"\n✅ Invoice generated successfully!")
        print(f"📄 File: {filename}")
        print(f"💰 Total: ${total:,.2f}")
        print(f"📁 Location: {os.path.abspath(filename)}")

    except Exception as e:
        print(f"❌ Error generating invoice: {e}")


# Quick invoice generation examples
def quick_examples():
    """Generate some example invoices"""
    generator = InvoiceGenerator()

    # Example 1: Basic invoice with defaults
    filename1, total1 = generator.create_invoice(
        invoice_number="2025-001",
        start_date="2025-01-01",
        end_date="2025-01-31"
    )
    print(f"Generated: {filename1} (${total1:,.2f})")

    # Example 2: Invoice with custom T&E
    custom_expenses = [
        {"description": "Monthly Retainer", "amount": 8000.00},
        {"description": "Insurance Stipend", "amount": 500.00},
        {"description": "Reimbursable T&E (Attached)", "amount": 2500.00},
        {"description": "Flight ORF-IAH", "amount": 518.49},
        {"description": "Hotel accommodation", "amount": 450.00},
    ]

    filename2, total2 = generator.create_invoice(
        invoice_number="2025-002",
        start_date="2025-02-01",
        end_date="2025-02-28",
        expenses=custom_expenses
    )
    print(f"Generated: {filename2} (${total2:,.2f})")


if __name__ == "__main__":
    # Run interactive mode
    main()

    # Uncomment to run examples instead:
    # quick_examples()