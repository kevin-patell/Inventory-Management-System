import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, Response, send_file
from flask_login import login_required
from sqlalchemy import func
from models import db, Product, Category, Supplier, PurchaseOrder, Sale, SaleItem, PurchaseItem, InventoryTransaction
from services.pdf_service import generate_inventory_report_pdf
from services.export_service import export_to_csv, export_to_excel
from config import Config

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    # Reports Hub
    all_products = Product.query.all()
    total_inventory_cost = sum(p.inventory_value for p in all_products)
    total_retail_value = sum(p.retail_value for p in all_products)
    potential_profit = total_retail_value - total_inventory_cost

    total_sales_revenue = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).filter(Sale.status == 'Completed').scalar()
    total_purchases_spent = db.session.query(func.coalesce(func.sum(PurchaseOrder.total_amount), 0.0)).filter(PurchaseOrder.status == 'Received').scalar()

    low_stock_count = sum(1 for p in all_products if p.is_low_stock)
    out_of_stock_count = sum(1 for p in all_products if p.is_out_of_stock)

    return render_template(
        'reports/index.html',
        total_inventory_cost=total_inventory_cost,
        total_retail_value=total_retail_value,
        potential_profit=potential_profit,
        total_sales_revenue=total_sales_revenue,
        total_purchases_spent=total_purchases_spent,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )

@reports_bp.route('/reports/stock')
@login_required
def stock_report():
    category_id = request.args.get('category_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    filter_status = request.args.get('status', 'all')

    query = Product.query

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)
    if filter_status == 'low':
        query = query.filter(Product.current_stock > 0, Product.current_stock <= Product.min_stock_level)
    elif filter_status == 'out':
        query = query.filter(Product.current_stock <= 0)

    products = query.order_by(Product.name).all()

    total_units = sum(p.current_stock for p in products)
    total_cost_val = sum(p.inventory_value for p in products)
    total_retail_val = sum(p.retail_value for p in products)

    # Check for PDF or export download
    export_format = request.args.get('export')
    if export_format == 'pdf':
        pdf_bytes = generate_inventory_report_pdf(products)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name="inventory_valuation_report.pdf"
        )
    elif export_format == 'csv':
        headers = ['SKU', 'Name', 'Category', 'Supplier', 'Stock', 'Min Level', 'Cost Price ($)', 'Retail Price ($)', 'Valuation ($)']
        rows = [[p.sku, p.name, p.category.name if p.category else '', p.supplier.name if p.supplier else '', p.current_stock, p.min_stock_level, f"{p.purchase_price:.2f}", f"{p.selling_price:.2f}", f"{p.inventory_value:.2f}"] for p in products]
        data = export_to_csv(headers, rows)
        return Response(data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=stock_valuation_report.csv"})
    elif export_format == 'excel':
        headers = ['SKU', 'Name', 'Category', 'Supplier', 'Stock', 'Min Level', 'Cost Price ($)', 'Retail Price ($)', 'Valuation ($)']
        rows = [[p.sku, p.name, p.category.name if p.category else '', p.supplier.name if p.supplier else '', p.current_stock, p.min_stock_level, p.purchase_price, p.selling_price, p.inventory_value] for p in products]
        data = export_to_excel("Stock Valuation Report", headers, rows)
        return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-disposition": "attachment; filename=stock_valuation_report.xlsx"})

    categories = Category.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()

    return render_template(
        'reports/stock_report.html',
        products=products,
        categories=categories,
        suppliers=suppliers,
        selected_category=category_id,
        selected_supplier=supplier_id,
        selected_status=filter_status,
        total_units=total_units,
        total_cost_val=total_cost_val,
        total_retail_val=total_retail_val
    )

@reports_bp.route('/reports/sales')
@login_required
def sales_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Sale.query.filter(Sale.status == 'Completed')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Sale.sale_date >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.sale_date < end_date)
        except ValueError:
            pass

    sales = query.order_by(Sale.sale_date.desc()).all()

    total_revenue = sum(s.total_amount for s in sales)
    total_profit = sum(s.gross_profit for s in sales)
    total_tax = sum(s.tax_amount for s in sales)
    total_discount = sum(s.discount_amount for s in sales)

    export_format = request.args.get('export')
    if export_format == 'csv':
        headers = ['Invoice Number', 'Date', 'Customer', 'Payment Method', 'Subtotal ($)', 'Discount ($)', 'Tax ($)', 'Total ($)', 'Profit ($)']
        rows = [[s.invoice_number, s.sale_date.strftime('%Y-%m-%d'), s.customer_name, s.payment_method, f"{s.subtotal:.2f}", f"{s.discount_amount:.2f}", f"{s.tax_amount:.2f}", f"{s.total_amount:.2f}", f"{s.gross_profit:.2f}"] for s in sales]
        data = export_to_csv(headers, rows)
        return Response(data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sales_report.csv"})

    return render_template(
        'reports/sales_report.html',
        sales=sales,
        start_date=start_date_str,
        end_date=end_date_str,
        total_revenue=total_revenue,
        total_profit=total_profit,
        total_tax=total_tax,
        total_discount=total_discount
    )

@reports_bp.route('/reports/purchases')
@login_required
def purchases_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    supplier_id = request.args.get('supplier_id', type=int)

    query = PurchaseOrder.query

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(PurchaseOrder.order_date >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(PurchaseOrder.order_date < end_date)
        except ValueError:
            pass

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    purchases = query.order_by(PurchaseOrder.order_date.desc()).all()

    total_spent = sum(p.total_amount for p in purchases if p.status == 'Received')
    suppliers = Supplier.query.order_by(Supplier.name).all()

    export_format = request.args.get('export')
    if export_format == 'csv':
        headers = ['PO Number', 'Date', 'Supplier', 'Status', 'Payment Status', 'Subtotal ($)', 'Tax ($)', 'Shipping ($)', 'Total ($)']
        rows = [[p.po_number, p.order_date.strftime('%Y-%m-%d'), p.supplier.name if p.supplier else '', p.status, p.payment_status, f"{p.subtotal:.2f}", f"{p.tax_amount:.2f}", f"{p.shipping_fee:.2f}", f"{p.total_amount:.2f}"] for p in purchases]
        data = export_to_csv(headers, rows)
        return Response(data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=purchases_report.csv"})

    return render_template(
        'reports/purchases_report.html',
        purchases=purchases,
        suppliers=suppliers,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_supplier=supplier_id,
        total_spent=total_spent
    )

@reports_bp.route('/reports/profit')
@login_required
def profit_report():
    # Overall profit calculation
    sales = Sale.query.filter(Sale.status == 'Completed').all()
    
    total_sales_revenue = sum(s.total_amount for s in sales)
    total_cogs = sum(s.total_cost for s in sales)
    gross_profit = total_sales_revenue - total_cogs
    profit_margin = round((gross_profit / total_sales_revenue * 100), 2) if total_sales_revenue > 0 else 0.0

    # Top selling products with profit contribution
    top_items = db.session.query(
        Product.name,
        Product.sku,
        func.sum(SaleItem.quantity).label('total_qty_sold'),
        func.sum(SaleItem.total_price).label('total_sales_val'),
        func.sum((SaleItem.unit_price - SaleItem.cost_price) * SaleItem.quantity).label('total_item_profit')
    ).join(SaleItem, Product.id == SaleItem.product_id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.status == 'Completed')\
     .group_by(Product.id)\
     .order_by(func.sum((SaleItem.unit_price - SaleItem.cost_price) * SaleItem.quantity).desc())\
     .limit(10).all()

    return render_template(
        'reports/profit_report.html',
        total_sales_revenue=total_sales_revenue,
        total_cogs=total_cogs,
        gross_profit=gross_profit,
        profit_margin=profit_margin,
        top_items=top_items
    )
