from datetime import datetime, timedelta
import random
from app import create_app
from models import (
    db, Role, User, Category, Supplier, Customer, Product,
    PurchaseOrder, PurchaseItem, Sale, SaleItem,
    InventoryTransaction, StockAdjustment, Notification, AuditLog
)

def seed_database():
    app = create_app()
    with app.app_context():
        # Clear existing tables cleanly
        db.drop_all()
        db.create_all()

        print("==> Database tables created.")

        # 1. Create Roles
        roles_data = [
            ('Admin', 'Full administrative access to manage all aspects, users, settings, and financials.'),
            ('Manager', 'Management access to products, suppliers, purchases, stock adjustments, and reports.'),
            ('Staff', 'Operational access to process sales, view inventory levels, and check stock.')
        ]
        role_objs = {}
        for name, desc in roles_data:
            role = Role(name=name, description=desc)
            db.session.add(role)
            role_objs[name] = role
        db.session.flush()

        # 2. Create Default Users
        users_data = [
            ('admin', 'admin@smartims.com', 'admin123', 'Alexander Wright', '+1 (555) 019-2831', role_objs['Admin']),
            ('manager', 'manager@smartims.com', 'manager123', 'Elena Rostova', '+1 (555) 018-7294', role_objs['Manager']),
            ('staff', 'staff@smartims.com', 'staff123', 'Marcus Vance', '+1 (555) 014-9912', role_objs['Staff'])
        ]
        user_objs = {}
        for username, email, pwd, fname, phone, role in users_data:
            user = User(
                username=username,
                email=email,
                full_name=fname,
                phone=phone,
                role=role,
                is_active=True,
                last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 12))
            )
            user.set_password(pwd)
            db.session.add(user)
            user_objs[username] = user
        db.session.flush()
        print("==> Roles and Users created.")

        # 3. Create Categories & Subcategories
        cat_electronics = Category(name='Electronics & Tech', description='Consumer electronics, gadgets and computing parts')
        cat_office = Category(name='Office Supplies', description='Paper products, stationery, desk organizers and furniture')
        cat_networking = Category(name='Networking & Telecom', description='Routers, switches, patch cables and accessories')
        cat_industrial = Category(name='Warehouse & Tools', description='Packaging materials, safety equipment and utility tools')

        db.session.add_all([cat_electronics, cat_office, cat_networking, cat_industrial])
        db.session.flush()

        # Subcategories
        sub_laptops = Category(name='Laptops & Desktops', description='Personal computers and laptops', parent_id=cat_electronics.id)
        sub_audio = Category(name='Audio & Headphones', description='Speakers, headsets, earphones', parent_id=cat_electronics.id)
        sub_stationery = Category(name='Desk Stationery', description='Pens, pads, organizers', parent_id=cat_office.id)
        sub_cables = Category(name='Cables & Adapters', description='Ethernet, HDMI, USB-C cables', parent_id=cat_networking.id)

        db.session.add_all([sub_laptops, sub_audio, sub_stationery, sub_cables])
        db.session.flush()
        print("==> Categories and Subcategories created.")

        # 4. Create Suppliers
        suppliers_data = [
            Supplier(
                name='Silicon Valley Tech Supply Co.',
                contact_person='David Chen',
                email='david.chen@svtechsupply.com',
                phone='+1 (408) 555-0144',
                address='400 Innovation Way, San Jose, CA',
                tax_number='TX-9948210',
                notes='Primary supplier for computer peripherals and microelectronics.'
            ),
            Supplier(
                name='Global Office Direct Wholesale',
                contact_person='Karen Bradley',
                email='kbradley@globalofficedirect.com',
                phone='+1 (312) 555-0189',
                address='1800 Michigan Ave, Chicago, IL',
                tax_number='TX-8839102',
                notes='Reliable bulk stationery and office supplies vendor.'
            ),
            Supplier(
                name='NextGen Logistics & Hardware Ltd',
                contact_person='Robert Sterling',
                email='rsterling@nextgenware.com',
                phone='+1 (206) 555-0177',
                address='742 Industrial Pkwy, Seattle, WA',
                tax_number='TX-7740192',
                notes='Networking hardware, heavy-duty cables, and warehouse tooling.'
            )
        ]
        db.session.add_all(suppliers_data)
        db.session.flush()
        print("==> Suppliers created.")

        # 5. Create Customers
        customers_data = [
            Customer(name='Acme Global Technologies', email='procure@acmeglobal.com', phone='+1 (555) 301-4401', address='100 Corporate Center, New York, NY'),
            Customer(name='Smart Design Studios', email='info@smartstudios.design', phone='+1 (555) 302-8820', address='55 Creative Way, Austin, TX'),
            Customer(name='CyberPulse Systems Inc.', email='billing@cyberpulse.io', phone='+1 (555) 303-9911', address='880 Tech Terrace, Boston, MA'),
            Customer(name='Sarah Jenkins', email='sarah.jenkins@gmail.com', phone='+1 (555) 404-1234', address='12 Oak Ridge Rd, Denver, CO'),
            Customer(name='Walk-in Retail Customer', email='retail@store.local', phone='', address='In-store Checkout')
        ]
        db.session.add_all(customers_data)
        db.session.flush()
        print("==> Customers created.")

        # 6. Create Products (A balanced mix: healthy stock, low stock, out of stock)
        products_data = [
            # Healthy Stock
            ('PRD-1001', 'UltraBook Pro 15" i7 16GB', 'High-performance laptop with 512GB SSD and 4K display', sub_laptops.id, suppliers_data[0].id, 750.00, 1099.00, 24, 5),
            ('PRD-1002', 'Wireless Noise-Canceling Headset', 'Over-ear Bluetooth headset with ANC and 30h battery', sub_audio.id, suppliers_data[0].id, 65.00, 129.99, 45, 10),
            ('PRD-1003', 'Mechanical RGB Gaming Keyboard', 'Hot-swappable tactile switches with aluminum frame', cat_electronics.id, suppliers_data[0].id, 42.00, 89.99, 38, 8),
            ('PRD-1004', 'Cat6 Shielded Ethernet Cable 50ft', 'High-speed gigabit snagless networking patch cable', sub_cables.id, suppliers_data[2].id, 6.50, 18.50, 80, 15),
            ('PRD-1005', 'Heavy-Duty Industrial Tape 6-Pack', 'Commercial packaging and sealing tape for parcels', cat_industrial.id, suppliers_data[2].id, 9.00, 24.00, 60, 12),
            ('PRD-1006', 'Executive Gel Pen Pack (12-Ct)', 'Smooth glide 0.7mm black ink quick-drying pens', sub_stationery.id, suppliers_data[1].id, 4.50, 12.99, 110, 20),

            # Low Stock Items (Trigger alerts!)
            ('PRD-1007', 'USB-C Multi-Port Hub 7-in-1', 'Aluminum dongle with 4K HDMI, SD Reader, 100W PD', sub_cables.id, suppliers_data[0].id, 22.00, 49.99, 4, 10), # Stock 4 <= Min 10
            ('PRD-1008', 'Ergonomic Mesh Task Chair', 'Adjustable lumbar support breathable office swivel chair', cat_office.id, suppliers_data[1].id, 110.00, 229.00, 3, 5),   # Stock 3 <= Min 5
            ('PRD-1009', 'Wi-Fi 6 Dual-Band Mesh Router', 'AX3000 gigabit wireless router for commercial use', cat_networking.id, suppliers_data[2].id, 55.00, 119.00, 2, 8),     # Stock 2 <= Min 8

            # Out of Stock Items (Trigger urgent alerts!)
            ('PRD-1010', '27-inch 4K UHD IPS Monitor', 'Frameless anti-glare professional desktop monitor', cat_electronics.id, suppliers_data[0].id, 210.00, 349.99, 0, 5), # Stock 0
            ('PRD-1011', 'Thermal Receipt Paper Rolls (50-Pk)', 'BPA-free 80mm high-grade thermal POS paper', cat_office.id, suppliers_data[1].id, 18.00, 39.99, 0, 10)       # Stock 0
        ]

        product_objs = []
        for sku, name, desc, cat_id, supp_id, p_price, s_price, stock, min_lvl in products_data:
            prod = Product(
                sku=sku,
                name=name,
                description=desc,
                category_id=cat_id,
                supplier_id=supp_id,
                purchase_price=p_price,
                selling_price=s_price,
                current_stock=stock,
                min_stock_level=min_lvl,
                image_url='default_product.png',
                status='Active'
            )
            db.session.add(prod)
            product_objs.append(prod)
        db.session.flush()
        print("==> Products created.")

        # 7. Create Historical Inventory Transactions for Initial Stock
        for p in product_objs:
            if p.current_stock > 0:
                txn = InventoryTransaction(
                    product_id=p.id,
                    transaction_type='stock_added',
                    quantity_change=p.current_stock,
                    previous_quantity=0,
                    new_quantity=p.current_stock,
                    reference_type='manual',
                    reference_id='INIT-STOCK',
                    reason='Opening warehouse balance initialization',
                    user_id=user_objs['admin'].id,
                    created_at=datetime.utcnow() - timedelta(days=20)
                )
                db.session.add(txn)

        # 8. Create Realistic Past Purchase Orders
        po1 = PurchaseOrder(
            po_number='PO-20260915-1082',
            supplier_id=suppliers_data[0].id,
            user_id=user_objs['manager'].id,
            order_date=datetime.utcnow() - timedelta(days=18),
            status='Received',
            payment_status='Paid',
            subtotal=7500.00,
            tax_amount=600.00,
            discount_amount=200.00,
            shipping_fee=150.00,
            total_amount=8050.00,
            notes='Quarterly bulk shipment of computing systems and peripherals.'
        )
        db.session.add(po1)
        db.session.flush()

        po1_item1 = PurchaseItem(purchase_id=po1.id, product_id=product_objs[0].id, quantity=10, unit_price=750.00, total_price=7500.00)
        db.session.add(po1_item1)

        po2 = PurchaseOrder(
            po_number='PO-20260928-3921',
            supplier_id=suppliers_data[1].id,
            user_id=user_objs['admin'].id,
            order_date=datetime.utcnow() - timedelta(days=5),
            status='Received',
            payment_status='Paid',
            subtotal=1100.00,
            tax_amount=88.00,
            discount_amount=0.00,
            shipping_fee=50.00,
            total_amount=1238.00,
            notes='Office furniture restock.'
        )
        db.session.add(po2)
        db.session.flush()

        po2_item1 = PurchaseItem(purchase_id=po2.id, product_id=product_objs[7].id, quantity=10, unit_price=110.00, total_price=1100.00)
        db.session.add(po2_item1)

        # Pending PO
        po3 = PurchaseOrder(
            po_number='PO-20261001-4418',
            supplier_id=suppliers_data[0].id,
            user_id=user_objs['manager'].id,
            order_date=datetime.utcnow() - timedelta(days=2),
            status='Pending',
            payment_status='Unpaid',
            subtotal=2100.00,
            tax_amount=168.00,
            discount_amount=50.00,
            shipping_fee=80.00,
            total_amount=2298.00,
            notes='Emergency replenishment for out-of-stock 27-inch monitors.'
        )
        db.session.add(po3)
        db.session.flush()
        po3_item1 = PurchaseItem(purchase_id=po3.id, product_id=product_objs[9].id, quantity=10, unit_price=210.00, total_price=2100.00)
        db.session.add(po3_item1)

        print("==> Purchase Orders and Items created.")

        # 9. Create Realistic Completed Sales Orders
        # Sale 1: Corporate Order
        sale1 = Sale(
            invoice_number='INV-20260920-5819',
            customer_id=customers_data[0].id,
            customer_name=customers_data[0].name,
            customer_phone=customers_data[0].phone,
            user_id=user_objs['staff'].id,
            sale_date=datetime.utcnow() - timedelta(days=12),
            status='Completed',
            payment_method='Bank Transfer',
            subtotal=3297.00,
            discount_amount=100.00,
            tax_amount=255.76,
            total_amount=3452.76,
            notes='IT workstation deployment order.'
        )
        db.session.add(sale1)
        db.session.flush()

        s1_item1 = SaleItem(sale_id=sale1.id, product_id=product_objs[0].id, quantity=3, unit_price=1099.00, cost_price=750.00, total_price=3297.00)
        db.session.add(s1_item1)

        txn_s1 = InventoryTransaction(
            product_id=product_objs[0].id,
            transaction_type='stock_removed',
            quantity_change=-3,
            previous_quantity=27,
            new_quantity=24,
            reference_type='sale',
            reference_id=sale1.invoice_number,
            reason=f"Sale order {sale1.invoice_number}",
            user_id=user_objs['staff'].id,
            created_at=sale1.sale_date
        )
        db.session.add(txn_s1)

        # Sale 2: Retail Customer
        sale2 = Sale(
            invoice_number='INV-20260929-7712',
            customer_id=customers_data[3].id,
            customer_name=customers_data[3].name,
            customer_phone=customers_data[3].phone,
            user_id=user_objs['staff'].id,
            sale_date=datetime.utcnow() - timedelta(days=4),
            status='Completed',
            payment_method='Card',
            subtotal=219.98,
            discount_amount=10.00,
            tax_amount=16.80,
            total_amount=226.78,
            notes='Accessories package.'
        )
        db.session.add(sale2)
        db.session.flush()

        s2_item1 = SaleItem(sale_id=sale2.id, product_id=product_objs[1].id, quantity=1, unit_price=129.99, cost_price=65.00, total_price=129.99)
        s2_item2 = SaleItem(sale_id=sale2.id, product_id=product_objs[2].id, quantity=1, unit_price=89.99, cost_price=42.00, total_price=89.99)
        db.session.add_all([s2_item1, s2_item2])

        # Sale 3: Today's Walk-in Sale
        sale3 = Sale(
            invoice_number='INV-20261003-9182',
            customer_id=customers_data[4].id,
            customer_name='Walk-in Retail Customer',
            customer_phone='',
            user_id=user_objs['staff'].id,
            sale_date=datetime.utcnow() - timedelta(hours=2),
            status='Completed',
            payment_method='Cash',
            subtotal=114.98,
            discount_amount=0.00,
            tax_amount=9.20,
            total_amount=124.18,
            notes='Counter purchase.'
        )
        db.session.add(sale3)
        db.session.flush()

        s3_item1 = SaleItem(sale_id=sale3.id, product_id=product_objs[3].id, quantity=2, unit_price=18.50, cost_price=6.50, total_price=37.00)
        s3_item2 = SaleItem(sale_id=sale3.id, product_id=product_objs[4].id, quantity=1, unit_price=24.00, cost_price=9.00, total_price=24.00)
        s3_item3 = SaleItem(sale_id=sale3.id, product_id=product_objs[2].id, quantity=1, unit_price=53.98, cost_price=42.00, total_price=53.98)
        db.session.add_all([s3_item1, s3_item2, s3_item3])

        print("==> Sales and POS records created.")

        # 10. Sample Stock Adjustment
        adj1 = StockAdjustment(
            adjustment_number='ADJ-20260925-1029',
            product_id=product_objs[4].id,
            adjustment_type='damaged',
            quantity=2,
            previous_quantity=62,
            new_quantity=60,
            reason='Boxes damaged by forklift during warehouse shelf relocation',
            user_id=user_objs['manager'].id,
            created_at=datetime.utcnow() - timedelta(days=8)
        )
        db.session.add(adj1)
        txn_adj = InventoryTransaction(
            product_id=product_objs[4].id,
            transaction_type='damaged_stock',
            quantity_change=-2,
            previous_quantity=62,
            new_quantity=60,
            reference_type='adjustment',
            reference_id=adj1.adjustment_number,
            reason='Forklift box crush damage',
            user_id=user_objs['manager'].id,
            created_at=adj1.created_at
        )
        db.session.add(txn_adj)

        # 11. Create Notifications
        notifs = [
            Notification(
                title='Out of Stock Alert: 27-inch 4K UHD Monitor',
                message='Inventory for PRD-1010 has depleted to 0 units. Reorder recommended immediately.',
                type='out_of_stock',
                link='/inventory/reorder',
                is_read=False,
                created_at=datetime.utcnow() - timedelta(hours=3)
            ),
            Notification(
                title='Low Stock Warning: USB-C Multi-Port Hub',
                message='PRD-1007 is down to 4 units (Threshold: 10).',
                type='low_stock',
                link='/inventory/reorder',
                is_read=False,
                created_at=datetime.utcnow() - timedelta(hours=5)
            ),
            Notification(
                title='New Purchase Order Created',
                message='Purchase Order PO-20261001-4418 for ₹2,298.00 has been sent to Silicon Valley Tech Supply.',
                type='purchase',
                link='/purchases/3',
                is_read=True,
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            Notification(
                title='Sale Invoice Completed',
                message='Invoice INV-20261003-9182 generated for Walk-in Retail Customer (₹124.18).',
                type='sale',
                link='/sales/3',
                is_read=False,
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
        ]
        db.session.add_all(notifs)

        # 12. Create Audit Logs
        audits = [
            AuditLog(username='admin', action='LOGIN', target_type='User', details='System Administrator signed into dashboard', created_at=datetime.utcnow() - timedelta(hours=1)),
            AuditLog(username='manager', action='STOCK_ADJUSTMENT', target_type='StockAdjustment', target_id=adj1.adjustment_number, details='Damaged stock deduction of 2 units on Heavy-Duty Industrial Tape', created_at=datetime.utcnow() - timedelta(days=8)),
            AuditLog(username='staff', action='SALE_CREATE', target_type='Sale', target_id='3', details='Processed counter sale invoice INV-20261003-9182 (₹124.18)', created_at=datetime.utcnow() - timedelta(hours=2)),
            AuditLog(username='admin', action='PRODUCT_CREATE', target_type='Product', target_id='1', details='Catalog item created: UltraBook Pro 15" i7 16GB', created_at=datetime.utcnow() - timedelta(days=20))
        ]
        db.session.add_all(audits)

        db.session.commit()
        print("==> Database successfully populated with initial production data!")
        print("\nDefault Accounts:")
        print("  Admin   : admin   / admin123")
        print("  Manager : manager / manager123")
        print("  Staff   : staff   / staff123\n")

if __name__ == '__main__':
    seed_database()
