import unittest
import json
from app import create_app
from models import db, User, Role, Product, Category, Supplier, Customer, PurchaseOrder, Sale, InventoryTransaction, StockAdjustment, Notification, AuditLog
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class InventorySystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed roles
        self.role_admin = Role(name='Admin', description='Administrator')
        self.role_manager = Role(name='Manager', description='Manager')
        self.role_staff = Role(name='Staff', description='Staff')
        db.session.add_all([self.role_admin, self.role_manager, self.role_staff])
        db.session.commit()

        # Create test users
        self.admin = User(username='admin', email='admin@test.com', full_name='Admin User', role=self.role_admin)
        self.admin.set_password('adminpass')

        self.manager = User(username='manager', email='manager@test.com', full_name='Manager User', role=self.role_manager)
        self.manager.set_password('managerpass')

        self.staff = User(username='staff', email='staff@test.com', full_name='Staff User', role=self.role_staff)
        self.staff.set_password('staffpass')

        db.session.add_all([self.admin, self.manager, self.staff])
        db.session.commit()

        # Seed category & supplier & product
        self.cat = Category(name='Hardware', description='Hardware parts')
        self.supp = Supplier(name='Global Supplies Ltd', email='supp@test.com', phone='555-1234')
        self.cust = Customer(name='Acme Testing Inc', email='cust@test.com')
        db.session.add_all([self.cat, self.supp, self.cust])
        db.session.commit()

        self.prod = Product(
            sku='PRD-TEST01',
            name='Test Wireless Mouse',
            category_id=self.cat.id,
            supplier_id=self.supp.id,
            purchase_price=10.0,
            selling_price=25.0,
            current_stock=20,
            min_stock_level=5,
            status='Active'
        )
        db.session.add(self.prod)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, username, password):
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_user_authentication(self):
        # Successful login
        resp = self.login('admin', 'adminpass')
        self.assertIn(b'Operations & Inventory Dashboard', resp.data)

        # Invalid login
        self.logout()
        resp = self.login('admin', 'wrongpass')
        self.assertIn(b'Invalid username/email or password', resp.data)

    def test_role_based_access(self):
        # Staff cannot access User Management (/users)
        self.login('staff', 'staffpass')
        resp = self.client.get('/users', follow_redirects=True)
        self.assertIn(b'Access denied', resp.data)

        # Admin can access User Management
        self.logout()
        self.login('admin', 'adminpass')
        resp = self.client.get('/users')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'System User Accounts', resp.data)

    def test_product_crud_and_sku(self):
        self.login('manager', 'managerpass')
        # Generate SKU endpoint
        resp = self.client.get('/products/generate-sku')
        data = json.loads(resp.data)
        self.assertTrue(data['sku'].startswith('PRD-'))

        # Add product
        resp = self.client.post('/products/create', data={
            'name': 'Ergonomic Keyboard',
            'sku': 'PRD-KEY01',
            'category_id': self.cat.id,
            'supplier_id': self.supp.id,
            'purchase_price': '30.00',
            'selling_price': '60.00',
            'current_stock': '15',
            'min_stock_level': '5',
            'status': 'Active'
        }, follow_redirects=True)
        self.assertIn(b'Ergonomic Keyboard', resp.data)
        
        # Verify in DB
        prod = Product.query.filter_by(sku='PRD-KEY01').first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.current_stock, 15)

    def test_purchase_order_and_stock_addition(self):
        self.login('manager', 'managerpass')
        initial_stock = self.prod.current_stock

        resp = self.client.post('/purchases/create', data={
            'supplier_id': self.supp.id,
            'status': 'Received',
            'payment_status': 'Paid',
            'discount_amount': '0',
            'tax_amount': '0',
            'shipping_fee': '0',
            'product_id[]': [str(self.prod.id)],
            'unit_price[]': ['12.00'],
            'quantity[]': ['10']
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify stock incremented by 10 (20 -> 30)
        prod = Product.query.get(self.prod.id)
        self.assertEqual(prod.current_stock, initial_stock + 10)

        # Verify InventoryTransaction logged
        txn = InventoryTransaction.query.filter_by(product_id=self.prod.id, transaction_type='stock_added').order_by(InventoryTransaction.id.desc()).first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.quantity_change, 10)

    def test_sale_order_and_stock_deduction(self):
        self.login('staff', 'staffpass')
        initial_stock = self.prod.current_stock # 20

        resp = self.client.post('/sales/create', data={
            'customer_id': str(self.cust.id),
            'customer_name': self.cust.name,
            'payment_method': 'Cash',
            'discount_amount': '0',
            'tax_amount': '0',
            'product_id[]': [str(self.prod.id)],
            'unit_price[]': ['25.00'],
            'quantity[]': ['3']
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify stock deducted by 3 (20 -> 17)
        prod = Product.query.get(self.prod.id)
        self.assertEqual(prod.current_stock, initial_stock - 3)

        # Verify Sale created
        sale = Sale.query.order_by(Sale.id.desc()).first()
        self.assertIsNotNone(sale)
        self.assertEqual(sale.total_amount, 75.0)

    def test_sale_return_restores_stock(self):
        self.login('manager', 'managerpass')
        # Create sale of 2 units
        self.client.post('/sales/create', data={
            'customer_id': '0',
            'customer_name': 'Walk-in Customer',
            'payment_method': 'Card',
            'product_id[]': [str(self.prod.id)],
            'unit_price[]': ['25.00'],
            'quantity[]': ['2']
        })
        prod = Product.query.get(self.prod.id)
        stock_after_sale = prod.current_stock

        sale = Sale.query.order_by(Sale.id.desc()).first()

        # Process return
        resp = self.client.post(f'/sales/{sale.id}/return', data={'return_reason': 'Defective cord'}, follow_redirects=True)
        self.assertIn(b'Returned', resp.data)

        # Verify stock restored (+2)
        prod = Product.query.get(self.prod.id)
        self.assertEqual(prod.current_stock, stock_after_sale + 2)

    def test_manual_stock_adjustment(self):
        self.login('manager', 'managerpass')
        resp = self.client.post('/inventory/adjust', data={
            'product_id': self.prod.id,
            'adjustment_type': 'recount',
            'quantity': '50',
            'reason': 'Annual physical audit count'
        }, follow_redirects=True)
        self.assertIn(b'Stock adjustment', resp.data)

        prod = Product.query.get(self.prod.id)
        self.assertEqual(prod.current_stock, 50)

    def test_low_stock_and_out_of_stock_alerts(self):
        self.login('manager', 'managerpass')
        # Adjust stock down to 3 (below min_stock_level 5)
        self.client.post('/inventory/adjust', data={
            'product_id': self.prod.id,
            'adjustment_type': 'recount',
            'quantity': '3',
            'reason': 'Audit reconciliation'
        })
        # Check notification created
        notif = Notification.query.filter_by(type='low_stock').first()
        self.assertIsNotNone(notif)
        self.assertIn('Low Stock Alert', notif.title)

        # Reorder Hub shows item
        resp = self.client.get('/inventory/reorder')
        self.assertIn(b'Low Stock', resp.data)
        self.assertIn(b'Test Wireless Mouse', resp.data)

    def test_rest_api(self):
        # GET /api/products
        resp = self.client.get('/api/products')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 1)

        # POST /api/products
        new_prod_data = {
            'name': 'API Optical Mouse',
            'category_id': self.cat.id,
            'purchase_price': 8.0,
            'selling_price': 18.0,
            'current_stock': 10,
            'min_stock_level': 4
        }
        resp = self.client.post('/api/products', json=new_prod_data)
        self.assertEqual(resp.status_code, 201)
        res_json = json.loads(resp.data)
        self.assertTrue(res_json['success'])

        # GET /api/reports/summary
        resp = self.client.get('/api/reports/summary')
        self.assertEqual(resp.status_code, 200)
        summary = json.loads(resp.data)['summary']
        self.assertIn('inventory_valuation', summary)

    def test_pdf_and_export_generation(self):
        self.login('admin', 'adminpass')
        # Stock PDF report
        resp = self.client.get('/reports/stock?export=pdf')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/pdf')

        # Excel export
        resp = self.client.get('/products/export/excel')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('spreadsheetml', resp.mimetype)

        # CSV export
        resp = self.client.get('/products/export/csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')

if __name__ == '__main__':
    unittest.main()
