from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo
from config import Config

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=25)])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='New passwords must match.')
    ])
    submit = SubmitField('Save Profile')

class UserAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=25)])
    role_id = SelectField('User Role', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Active Account', default=True)
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Save User')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    sku = StringField('SKU / Barcode', validators=[DataRequired(), Length(max=64)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    supplier_id = SelectField('Preferred Supplier', coerce=int, validators=[Optional()])
    purchase_price = DecimalField('Cost / Purchase Price ($)', places=2, validators=[DataRequired(), NumberRange(min=0)])
    selling_price = DecimalField('Selling / Retail Price ($)', places=2, validators=[DataRequired(), NumberRange(min=0)])
    current_stock = IntegerField('Initial Stock Quantity', validators=[DataRequired(), NumberRange(min=0)], default=0)
    min_stock_level = IntegerField('Minimum Reorder Level', validators=[DataRequired(), NumberRange(min=0)], default=10)
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Status', choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Discontinued', 'Discontinued')], default='Active')
    image = FileField('Product Image', validators=[Optional(), FileAllowed(list(Config.ALLOWED_EXTENSIONS), 'Images only!')])
    submit = SubmitField('Save Product')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    parent_id = SelectField('Parent Category (Optional)', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')

class SupplierForm(FlaskForm):
    name = StringField('Supplier / Company Name', validators=[DataRequired(), Length(max=150)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    address = TextAreaField('Address', validators=[Optional()])
    tax_number = StringField('Tax / GST / VAT Number', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_active = BooleanField('Active Supplier', default=True)
    submit = SubmitField('Save Supplier')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    address = TextAreaField('Billing / Shipping Address', validators=[Optional()])
    submit = SubmitField('Save Customer')

class StockAdjustmentForm(FlaskForm):
    product_id = SelectField('Select Product', coerce=int, validators=[DataRequired()])
    adjustment_type = SelectField('Adjustment Type', choices=[
        ('add', 'Add Stock (+ Increase)'),
        ('subtract', 'Subtract Stock (- Decrease)'),
        ('damaged', 'Damaged / Spoiled Goods (- Decrease)'),
        ('recount', 'Inventory Recount (Set Exact Quantity)')
    ], validators=[DataRequired()])
    quantity = IntegerField('Quantity / Count', validators=[DataRequired(), NumberRange(min=0)])
    reason = TextAreaField('Reason / Note', validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField('Apply Adjustment')
