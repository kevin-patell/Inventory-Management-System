# Apex Global Inventory Management System

A modern, production-grade **Inventory Management System (IMS)** built with **Python, Flask, SQLite, Bootstrap 5, and JavaScript**. Designed for small-to-medium enterprises (SMEs) to track products, suppliers, customers, purchases, sales, warehouse stock movements, and financial profit analytics from a single, unified web application.

---

## 🌟 Key Features

### 1. Authentication & Role-Based Access Control (RBAC)
- **Secure Password Hashing**: Utilizes industry-standard PBKDF2/SHA256 password hashing via Werkzeug.
- **Three Core Roles**:
  - **Admin**: Full administrative privileges over users, roles, audit trails, and all modules.
  - **Manager**: Manage products, suppliers, purchase orders, manual stock adjustments, and view reports.
  - **Staff**: Operational access to process customer sales (POS), lookup stock availability, and review records.
- **Session Management**: Session cookies with Flask-Login and CSRF protection on forms.
- **User Profile & Security**: Update contact info and change passwords securely.

### 2. Executive Dashboard & Visual Analytics
- **Live KPI Metrics**: Total products, categories, suppliers, inventory valuation (cost price), retail valuation, today's sales, monthly sales, and active stock alert counts.
- **Interactive Chart.js Visualizations**:
  - 7-Day daily revenue trend area chart.
  - Category share doughnut distribution.
  - Inventory transaction volume by type bar chart.
- **Urgent Reorder Radar**: Highlights products at or below minimum threshold with 1-click reorder actions.
- **Recent Activities**: Live feeds of recent sales, purchases, and ledger movements.

### 3. Comprehensive Product Catalog
- **Full CRUD**: Create, view, update, and safely deactivate or delete products.
- **Smart SKU Generator**: 1-click generation of unique SKUs (`PRD-XXXXX`).
- **Product Media Uploads**: Secure file upload validation for images.
- **Advanced Filtering**: Live search by product name/SKU, category filter, supplier filter, stock level status filter, and multi-column sorting.
- **Pagination**: Optimized server-side pagination.

### 4. Category & Supplier Management
- **Hierarchical Categories**: Support for parent categories and subcategories.
- **Supplier Directory**: Track vendor contacts, emails, phone numbers, tax IDs, and payment terms.
- **Vendor-Specific Insights**: Drill down into vendor purchase history and inventory valuation of items supplied.

### 5. Procurement / Purchase Management (Stock-In)
- **Multi-Line Purchase Orders**: Add multiple line items with live unit cost and row total calculations.
- **Fulfillment Workflows**:
  - **Received**: Automatically increments stock in warehouse and generates movement ledger entries.
  - **Pending**: Track incoming consignments; receive or cancel when goods arrive.
- **Financial Calculation**: Subtotal, percentage/fixed discounts, sales tax, and freight fees.
- **Printable & PDF POs**: Instant ReportLab PDF generation and printable invoices.

### 6. Sales / POS Checkout (Stock-Out)
- **Point of Sale (POS) Interface**: Dynamic multi-item order builder with real-time stock validation (prevents overselling).
- **Customer Association**: Link to existing customer accounts or process walk-in counter sales.
- **Automated Stock Deduction**: Deducts warehouse inventory immediately and records transaction audit trails.
- **Customer Returns**: 1-click return workflow that restores stock back to inventory and logs reasons.
- **Invoicing**: Printable receipt and PDF tax invoice generation.

### 7. Advanced Inventory Movement Ledger & Adjustments
- **Immutable Transaction Ledger**: Tracks every stock change with before-and-after quantities, timestamp, reference number, reason, and user ID.
- **Transaction Types**: `stock_added`, `stock_removed`, `stock_returned`, `damaged_stock`, `adjustment_add`, `adjustment_sub`.
- **Manual Stock Adjustments**: Easily adjust quantities for damage, spoiled goods, or periodic audit recounts.

### 8. Automated Low-Stock & Reorder Hub
- **Threshold Detection**: Automatically detects items where `current_stock <= min_stock_level`.
- **Suggested Order Quantities**: Calculates recommended replenishment levels `(min_stock_level * 2) - current_stock`.
- **1-Click Purchase Order**: Pre-populates a new PO directly from the reorder radar.

### 9. Business Intelligence & Reports
- **Stock Valuation Report**: Valuation breakdown by cost and retail value with category/supplier filters.
- **Sales Performance Report**: Revenue, discount, tax, and profit breakdowns by custom date range.
- **Purchases Report**: Total spend and order counts by supplier and date range.
- **Profit & Loss Analytics**: Revenue vs Cost of Goods Sold (COGS), gross profit margin %, and ranking of top margin-contributing products.

### 10. Document Generation & Data Export
- **PDF Generation**: Invoices, purchase orders, and valuation reports generated via **ReportLab**.
- **Excel (.xlsx) Export**: Formatted workbooks with styled headers and auto-width columns via **openpyxl**.
- **CSV Export**: Clean CSV exports for products, sales, purchases, and stock ledgers.
- **Printable Layouts**: Optimized `@media print` stylesheets for standard printers.

### 11. Security, Audit Logs & In-App Notifications
- **In-App Notifications**: Real-time notification badge in top navigation bar for low stock, out of stock, purchase orders, and sales.
- **System Audit Trail**: Complete log of user actions (`LOGIN`, `LOGOUT`, `PRODUCT_CREATE`, `SALE_CREATE`, `STOCK_ADJUSTMENT`, etc.) with IP addresses.
- **Security**: Flask-WTF CSRF protection, SQL injection prevention via SQLAlchemy parameterized queries, role decorators.

### 12. REST API
- Clean JSON REST API endpoints under `/api/` for integration with mobile apps, external POS hardware, or third-party ERPs.

---

## 💻 Technology Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.11, Flask 3.0+ |
| **Database ORM** | Flask-SQLAlchemy 3.1+, SQLite |
| **Authentication** | Flask-Login 0.6+, Werkzeug Security |
| **Form Handling & CSRF** | Flask-WTF 1.3+, WTForms 3.2+ |
| **PDF Generation** | ReportLab 5.0+ |
| **Spreadsheet Generation** | openpyxl 3.1+ |
| **Frontend UI** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons |
| **Charting Engine** | Chart.js 4.4+ |
| **Testing** | unittest, Flask test client |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Installation
Clone or navigate to the project directory:
```bash
cd "Inventory Management System"
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Run the seed script to create all SQLite database tables and populate sample products, suppliers, customers, and test orders:
```bash
python seed.py
```

### 4. Run Application
Start the Flask development server:
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default User Accounts

The database comes pre-seeded with three accounts demonstrating each role:

| Role | Username | Password | Full Name | Permissions |
|---|---|---|---|---|
| **Admin** | `admin` | `admin123` | Alexander Wright | Full access (Users, Audit, System, Financials) |
| **Manager** | `manager` | `manager123` | Elena Rostova | Catalog, Suppliers, Purchases, Adjustments, Reports |
| **Staff** | `staff` | `staff123` | Marcus Vance | Sales / POS checkout, Catalog view, Customer view |

*(Note: On the login screen, you can also click the demo credential buttons to autofill these credentials instantly!)*

---

## 📁 Project Structure

```text
Inventory Management System/
│
├── app.py                      # Application entry point & factory
├── config.py                   # App configuration & environment settings
├── forms.py                    # Flask-WTF form classes & validation
├── requirements.txt            # Python dependencies
├── seed.py                     # Initial seed database script
├── test_system.py              # Automated test suite
├── README.md                   # Documentation
│
├── models/                     # SQLAlchemy Models
│   ├── __init__.py             # DB instance & model exports
│   ├── user.py                 # User & Role models
│   ├── product.py              # Product, Category, Supplier, Customer
│   ├── purchase.py             # PurchaseOrder & PurchaseItem
│   ├── sale.py                 # Sale & SaleItem
│   ├── inventory.py            # InventoryTransaction & StockAdjustment
│   └── audit.py                # AuditLog & Notification
│
├── routes/                     # Blueprint Route Controllers
│   ├── __init__.py
│   ├── auth.py                 # Login, logout, profile
│   ├── dashboard.py            # Dashboard metrics & Chart.js API
│   ├── products.py             # Product CRUD, SKU generator, exports
│   ├── categories.py           # Categories & subcategories
│   ├── suppliers.py            # Supplier management
│   ├── customers.py            # Customer directory
│   ├── purchases.py            # Purchase order creation, invoicing, PDF
│   ├── sales.py                # Sales / POS, stock deduction, returns, PDF
│   ├── inventory.py            # Stock movement ledger & reorder hub
│   ├── reports.py              # Valuation, Sales, Purchases & Profit reports
│   ├── audit.py                # System activity audit logs
│   ├── notifications.py        # In-app notifications
│   ├── users.py                # Admin user management
│   └── api.py                  # REST API endpoints
│
├── services/                   # Business Logic & Utilities
│   ├── __init__.py
│   ├── inventory_service.py    # Stock calculation & alert triggering
│   ├── pdf_service.py          # ReportLab PDF invoice & report generation
│   ├── export_service.py       # CSV and Excel export generators
│   └── audit_service.py        # Audit logging & notification dispatch
│
├── utils/                      # Helper Functions & Decorators
│   ├── __init__.py
│   ├── decorators.py           # Role permission decorators (@role_required)
│   └── helpers.py              # SKU generator, date & currency formatters
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Main layout (sidebar, navbar, alerts)
│   ├── auth/                   # Login & profile templates
│   ├── dashboard/              # Analytics dashboard
│   ├── products/               # Products list, form, view
│   ├── categories/             # Categories tree & edit
│   ├── suppliers/              # Supplier directory & profile
│   ├── customers/              # Customer directory & orders
│   ├── purchases/              # PO list, builder, invoice view
│   ├── sales/                  # Sales list, POS checkout, invoice view
│   ├── inventory/              # Movement ledger, adjustments, reorder hub
│   ├── reports/                # Financial and valuation reports
│   ├── audit/                  # Audit trail viewer
│   ├── notifications/          # In-app notifications page
│   ├── users/                  # User accounts list and edit
│   └── errors/                 # 403, 404, 500 pages
│
├── static/                     # Static Web Assets
│   ├── css/
│   │   └── style.css           # Modern design system & print styles
│   ├── js/
│   │   ├── main.js             # General UI, notification polling, alerts
│   │   ├── dashboard.js        # Dynamic Chart.js visualizations
│   │   └── pos.js              # POS & Purchase order dynamic line items
│   ├── images/
│   └── uploads/
│       └── products/           # Uploaded product images
│
└── database/
    └── inventory.db            # SQLite database file
```

---

## 📡 REST API Reference

The application provides a RESTful API under the `/api` namespace with JSON responses:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products` | Retrieve all products (supports `?search=`, `?category_id=`, `?stock_status=`) |
| `GET` | `/api/products/<id>` | Retrieve single product details |
| `POST` | `/api/products` | Create a new product |
| `PUT` | `/api/products/<id>` | Update an existing product |
| `DELETE` | `/api/products/<id>` | Deactivate or delete product |
| `GET` | `/api/categories` | List all categories |
| `POST` | `/api/categories` | Create a new category |
| `GET` | `/api/suppliers` | List all suppliers |
| `POST` | `/api/suppliers` | Create a new supplier |
| `POST` | `/api/stock/adjust` | Record manual stock adjustment |
| `GET` | `/api/purchases` | Retrieve recent purchase orders |
| `POST` | `/api/purchases` | Create purchase order (adds stock if Received) |
| `GET` | `/api/sales` | Retrieve recent sales orders |
| `POST` | `/api/sales` | Create sale order (validates and deducts stock) |
| `GET` | `/api/reports/summary` | Summary KPIs (total products, valuation, sales, profit) |

---

## 🧪 Running Automated Tests

A test suite verifying authentication, RBAC, inventory logic, POS, purchases, ReportLab PDF, openpyxl Excel, and REST API is included in `test_system.py`:
```bash
python test_system.py
```

---

## 📄 License
This project is open-source under the MIT License.
