import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import Config

def get_pdf_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a')
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    bold_body_style = ParagraphStyle(
        'DocBoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'heading': heading_style,
        'body': body_style,
        'bold': bold_body_style
    }

def generate_sales_invoice_pdf(sale):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    pdf_currency = getattr(Config, 'PDF_CURRENCY_SYMBOL', 'Rs. ')
    story = []

    # Header Section
    header_data = [
        [
            Paragraph(f"<b>{Config.COMPANY_NAME}</b><br/>{Config.COMPANY_ADDRESS}<br/>Phone: {Config.COMPANY_PHONE} | Email: {Config.COMPANY_EMAIL}", styles['body']),
            Paragraph(f"<b>SALES INVOICE</b><br/><font size='12' color='#4338ca'><b>{sale.invoice_number}</b></font><br/>Date: {sale.sale_date.strftime('%b %d, %Y %H:%M')}", styles['bold'])
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=15))

    # Customer & Order Details
    customer_info = f"<b>Billed To:</b><br/>{sale.customer_name or 'Walk-in Customer'}"
    if sale.customer and sale.customer.phone:
        customer_info += f"<br/>Phone: {sale.customer.phone}"
    if sale.customer and sale.customer.email:
        customer_info += f"<br/>Email: {sale.customer.email}"

    order_info = f"<b>Payment Method:</b> {sale.payment_method}<br/>"
    order_info += f"<b>Status:</b> {sale.status.upper()}<br/>"
    order_info += f"<b>Cashier / Rep:</b> {sale.user.full_name if sale.user else 'Staff'}"

    details_data = [
        [Paragraph(customer_info, styles['body']), Paragraph(order_info, styles['body'])]
    ]
    details_table = Table(details_data, colWidths=[270, 270])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 20))

    # Line Items Table
    items_data = [
        ['#', 'Item Description / SKU', 'Unit Price', 'Qty', 'Total']
    ]
    for idx, item in enumerate(sale.items, 1):
        item_desc = f"<b>{item.product.name}</b><br/><font color='#64748b' size='8'>SKU: {item.product.sku}</font>"
        items_data.append([
            str(idx),
            Paragraph(item_desc, styles['body']),
            f"{pdf_currency}{item.unit_price:.2f}",
            str(item.quantity),
            f"{pdf_currency}{item.total_price:.2f}"
        ])

    items_table = Table(items_data, colWidths=[30, 270, 80, 50, 110])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(items_table)
    story.append(Spacer(1, 15))

    # Totals Summary Table
    totals_data = [
        ['Subtotal:', f"{pdf_currency}{sale.subtotal:.2f}"],
        ['Discount:', f"-{pdf_currency}{sale.discount_amount:.2f}"],
        ['Tax (GST/VAT):', f"+{pdf_currency}{sale.tax_amount:.2f}"],
        ['Grand Total:', f"{pdf_currency}{sale.total_amount:.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[430, 110])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 12),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#4338ca')),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#4338ca')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(totals_table)

    # Footer Notes
    story.append(Spacer(1, 25))
    if sale.notes:
        story.append(Paragraph(f"<b>Notes:</b> {sale.notes}", styles['body']))
        story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph("Thank you for your business! For any questions regarding this invoice, please reach out to our billing support.", styles['subtitle']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_purchase_order_pdf(purchase):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    pdf_currency = getattr(Config, 'PDF_CURRENCY_SYMBOL', 'Rs. ')
    story = []

    # Header
    header_data = [
        [
            Paragraph(f"<b>{Config.COMPANY_NAME}</b><br/>{Config.COMPANY_ADDRESS}<br/>Phone: {Config.COMPANY_PHONE} | Email: {Config.COMPANY_EMAIL}", styles['body']),
            Paragraph(f"<b>PURCHASE ORDER</b><br/><font size='12' color='#0284c7'><b>{purchase.po_number}</b></font><br/>Date: {purchase.order_date.strftime('%b %d, %Y')}", styles['bold'])
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=15))

    # Supplier Info
    supp = purchase.supplier
    supplier_info = f"<b>Supplier:</b><br/><b>{supp.name}</b>"
    if supp.contact_person:
        supplier_info += f"<br/>Attn: {supp.contact_person}"
    if supp.email:
        supplier_info += f"<br/>Email: {supp.email}"
    if supp.phone:
        supplier_info += f"<br/>Phone: {supp.phone}"
    if supp.address:
        supplier_info += f"<br/>Address: {supp.address}"

    order_info = f"<b>PO Status:</b> {purchase.status.upper()}<br/>"
    order_info += f"<b>Payment Status:</b> {purchase.payment_status.upper()}<br/>"
    order_info += f"<b>Purchaser:</b> {purchase.user.full_name if purchase.user else 'Authorized Staff'}"

    details_data = [
        [Paragraph(supplier_info, styles['body']), Paragraph(order_info, styles['body'])]
    ]
    details_table = Table(details_data, colWidths=[270, 270])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bae6fd')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 20))

    # Items
    items_data = [
        ['#', 'Item Description / SKU', 'Unit Cost', 'Qty Ordered', 'Total Cost']
    ]
    for idx, item in enumerate(purchase.items, 1):
        item_desc = f"<b>{item.product.name}</b><br/><font color='#64748b' size='8'>SKU: {item.product.sku}</font>"
        items_data.append([
            str(idx),
            Paragraph(item_desc, styles['body']),
            f"{pdf_currency}{item.unit_price:.2f}",
            str(item.quantity),
            f"{pdf_currency}{item.total_price:.2f}"
        ])

    items_table = Table(items_data, colWidths=[30, 270, 80, 50, 110])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(items_table)
    story.append(Spacer(1, 15))

    # Totals
    totals_data = [
        ['Subtotal:', f"{pdf_currency}{purchase.subtotal:.2f}"],
        ['Discount:', f"-{pdf_currency}{purchase.discount_amount:.2f}"],
        ['Tax:', f"+{pdf_currency}{purchase.tax_amount:.2f}"],
        ['Shipping:', f"+{pdf_currency}{purchase.shipping_fee:.2f}"],
        ['Total Order Amount:', f"{pdf_currency}{purchase.total_amount:.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[430, 110])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 12),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#0369a1')),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#0369a1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(totals_table)

    story.append(Spacer(1, 25))
    if purchase.notes:
        story.append(Paragraph(f"<b>Notes:</b> {purchase.notes}", styles['body']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_inventory_report_pdf(products, title="Inventory Valuation & Stock Report"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = get_pdf_styles()
    pdf_currency = getattr(Config, 'PDF_CURRENCY_SYMBOL', 'Rs. ')
    story = []

    # Title
    story.append(Paragraph(f"<b>{Config.COMPANY_NAME}</b>", styles['subtitle']))
    story.append(Paragraph(title, styles['title']))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}", styles['subtitle']))
    story.append(Spacer(1, 15))

    # Summary
    total_qty = sum(p.current_stock for p in products)
    total_cost_val = sum(p.inventory_value for p in products)
    total_retail_val = sum(p.retail_value for p in products)

    summary_data = [
        [
            f"Total SKUs: {len(products)}",
            f"Total Units in Stock: {total_qty}",
            f"Total Cost Valuation: {pdf_currency}{total_cost_val:,.2f}",
            f"Total Retail Value: {pdf_currency}{total_retail_val:,.2f}"
        ]
    ]
    summary_table = Table(summary_data, colWidths=[120, 130, 145, 145])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Products Table
    headers = ['SKU', 'Product Name', 'Category', 'Stock', 'Unit Cost', 'Unit Price', 'Total Value']
    table_data = [headers]

    for p in products:
        table_data.append([
            p.sku,
            Paragraph(p.name[:35], styles['body']),
            p.category.name if p.category else 'N/A',
            str(p.current_stock),
            f"{pdf_currency}{p.purchase_price:.2f}",
            f"{pdf_currency}{p.selling_price:.2f}",
            f"{pdf_currency}{p.inventory_value:.2f}"
        ])

    table = Table(table_data, colWidths=[70, 180, 80, 45, 55, 55, 55])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
