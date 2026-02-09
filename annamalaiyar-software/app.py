from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_mysqldb import MySQL 
import MySQLdb
from datetime import datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
from flask import send_file  # Add this to your existing imports

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=30)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_NAME')

mysql = MySQL(app)

# Load translations
def load_translations(lang='en'):
    try:
        with open(f'static/translations/{lang}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Return English as fallback
        with open('static/translations/en.json', 'r', encoding='utf-8') as f:
            return json.load(f)

# Helper Functions
def get_db_connection():
    return mysql.connection

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def is_admin_logged_in():
    return 'admin_id' in session

# Before each request
@app.before_request
def before_request():
    # Set language
    if 'lang' not in session:
        session['lang'] = 'en'
    
    # Auto logout for admin after inactivity
    if 'admin_id' in session:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        session.modified = True

# Email Configuration
EMAIL_CONFIG = {
    'host': os.getenv('EMAIL_HOST'),
    'port': int(os.getenv('EMAIL_PORT')),
    'username': os.getenv('EMAIL_USERNAME'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'admin_email': os.getenv('ADMIN_EMAIL')
}


def send_email(to_email, subject, html_content, plain_text):
    """Send email using SMTP configuration"""
    try:
        # For now, just print the email details
        print(f"📧 Email would be sent to: {to_email}")
        print(f"📋 Subject: {subject}")
        print(f"📄 Plain text preview: {plain_text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
    
# Customer Routes
@app.route('/')
def home():
    translations = load_translations(session.get('lang', 'en'))
    
    # Get featured products and courses
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Featured products
    cur.execute("SELECT * FROM products WHERE is_featured = TRUE ORDER BY created_at DESC LIMIT 6")
    featured_products = cur.fetchall()
    
    # Featured courses
    cur.execute("SELECT * FROM courses WHERE is_featured = TRUE ORDER BY created_at DESC LIMIT 6")
    featured_courses = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/index.html', 
                         translations=translations,
                         featured_products=featured_products,
                         featured_courses=featured_courses,
                         lang=session.get('lang', 'en'))

@app.route('/products')
def products():
    translations = load_translations(session.get('lang', 'en'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products ORDER BY name")
    products_list = cur.fetchall()
    cur.close()
    
    return render_template('customer/products.html',
                         translations=translations,
                         products=products_list,
                         lang=session.get('lang', 'en'))

@app.route('/courses')
def courses():
    translations = load_translations(session.get('lang', 'en'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM courses ORDER BY name")
    courses_list = cur.fetchall()
    cur.close()
    
    return render_template('customer/courses.html',
                         translations=translations,
                         courses=courses_list,
                         lang=session.get('lang', 'en'))

@app.route('/order', methods=['GET', 'POST'])
def order():
    translations = load_translations(session.get('lang', 'en'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        phone = request.form['phone']
        email = request.form.get('email', '')
        address = request.form['address']
        item_type = request.form['item_type']
        item_id = request.form['item_id']
        quantity = int(request.form.get('quantity', 1))
        
        # Calculate price
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if item_type == 'product':
            cur.execute("SELECT price FROM products WHERE id = %s", (item_id,))
            result = cur.fetchone()
            price = result['price'] if result else 0  # Changed from result[0]
        else:
            cur.execute("SELECT price FROM courses WHERE id = %s", (item_id,))
            result = cur.fetchone()
            price = result['price'] if result else 0  # Changed from result[0]
        
        total_price = price * quantity
        
        # Save customer
        cur.execute("""
            INSERT INTO customers (name, phone, email, address)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, address))
        customer_id = cur.lastrowid
        
        # Save order
        if item_type == 'product':
            cur.execute("""
                INSERT INTO orders (customer_id, product_id, quantity, total_price)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, item_id, quantity, total_price))
        else:
            cur.execute("""
                INSERT INTO orders (customer_id, course_id, quantity, total_price)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, item_id, quantity, total_price))
        
        order_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        send_new_order_notification(order_id)
        
        # Flash success message
        flash(translations['order_success'], 'success')
        return redirect(url_for('home'))
    
    # GET request - show order form
    item_type = request.args.get('type')
    item_id = request.args.get('id')
    
    if not item_type or not item_id:
        return redirect(url_for('home'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if item_type == 'product':
        cur.execute("SELECT * FROM products WHERE id = %s", (item_id,))
        item = cur.fetchone()
        item_name = 'Product'
    else:
        cur.execute("SELECT * FROM courses WHERE id = %s", (item_id,))
        item = cur.fetchone()
        item_name = 'Course'
    
    cur.close()
    
    if not item:
        return redirect(url_for('home'))
    
    return render_template('customer/order.html',
                         translations=translations,
                         item=item,
                         item_type=item_type,
                         item_id=item_id,
                         item_name=item_name,
                         lang=session.get('lang', 'en'))

@app.route('/change_language/<lang>')
def change_language(lang):
    if lang in ['en', 'ta']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))


# ==================== ADMIN AUTHENTICATION ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id, username, password_hash FROM admin WHERE username = %s", (username,))
        admin = cur.fetchone()
        cur.close()
        
        if admin and check_password(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get statistics - use dictionary keys
    cur.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM orders WHERE payment_status = 'Pending'")
    pending_payments = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Delivered'")
    delivered_orders = cur.fetchone()['count']
    
    cur.execute("SELECT SUM(total_price) as total FROM orders WHERE payment_status = 'Paid'")
    total_sales_result = cur.fetchone()
    total_sales = total_sales_result['total'] or 0 if total_sales_result else 0    
    # Recent orders with customer details
    cur.execute("""
        SELECT o.id, c.name, c.phone, o.total_price, o.payment_status, 
               o.delivery_status, o.order_date,
               COALESCE(p.name, cs.name) as item_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        ORDER BY o.order_date DESC
        LIMIT 10
    """)
    recent_orders = cur.fetchall()
    
    # Daily sales
    cur.execute("""
        SELECT DATE(order_date) as date, SUM(total_price) as daily_sales
        FROM orders 
        WHERE payment_status = 'Paid'
        AND order_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(order_date)
        ORDER BY date
    """)
    daily_sales = cur.fetchall()
    
    cur.close()
    
    return render_template('admin/dashboard.html',
                         total_orders=total_orders,
                         pending_payments=pending_payments,
                         delivered_orders=delivered_orders,
                         total_sales=total_sales,
                         recent_orders=recent_orders,
                         daily_sales=daily_sales)

# ==================== PRODUCT MANAGEMENT ====================
@app.route('/admin/products')
def admin_products():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    cur.close()
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/api/product', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_product():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # Get single product
        product_id = request.args.get('id')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()
        
        if product:
            return jsonify({
                'id': product[0],
                'name': product[1],
                'description': product[2],
                'price': float(product[3]),
                'stock': product[4],
                'image_path': product[5],
                'is_featured': bool(product[6])
            })
        return jsonify({'error': 'Product not found'}), 404
    
    elif request.method == 'POST':
        # Create new product
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        is_featured = request.form.get('is_featured') == 'true'
        
        # Handle file upload
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_path = filename
                image.save(os.path.join('static/uploads', filename))
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO products (name, description, price, stock, image_path, is_featured)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, description, price, stock, image_path, is_featured))
        mysql.connection.commit()
        product_id = cur.lastrowid
        cur.close()
        
        return jsonify({'success': True, 'id': product_id})
    
    elif request.method == 'PUT':
        # Update product
        data = request.get_json()
        product_id = data.get('id')
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        stock = data.get('stock')
        is_featured = data.get('is_featured', False)
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            UPDATE products 
            SET name = %s, description = %s, price = %s, stock = %s, is_featured = %s, updated_at = NOW()
            WHERE id = %s
        """, (name, description, price, stock, is_featured, product_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Delete product
        product_id = request.args.get('id')
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})

# ==================== COURSE MANAGEMENT ====================
@app.route('/admin/courses')
def admin_courses():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM courses ORDER BY created_at DESC")
    courses = cur.fetchall()
    cur.close()
    
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/api/course', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_course():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # Get single course
        course_id = request.args.get('id')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        cur.close()
        
        if course:
            return jsonify({
                'id': course[0],
                'name': course[1],
                'description': course[2],
                'duration': course[3],
                'price': float(course[4]),
                'seats': course[5],
                'image_path': course[6],
                'is_featured': bool(course[7])
            })
        return jsonify({'error': 'Course not found'}), 404
    
    elif request.method == 'POST':
        # Create new course
        name = request.form.get('name')
        description = request.form.get('description')
        duration = request.form.get('duration')
        price = request.form.get('price')
        seats = request.form.get('seats')
        is_featured = request.form.get('is_featured') == 'true'
        
        # Handle file upload
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_path = filename
                image.save(os.path.join('static/uploads', filename))
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO courses (name, description, duration, price, seats, image_path, is_featured)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, description, duration, price, seats, image_path, is_featured))
        mysql.connection.commit()
        course_id = cur.lastrowid
        cur.close()
        
        return jsonify({'success': True, 'id': course_id})
    
    elif request.method == 'PUT':
        # Update course
        data = request.get_json()
        course_id = data.get('id')
        name = data.get('name')
        description = data.get('description')
        duration = data.get('duration')
        price = data.get('price')
        seats = data.get('seats')
        is_featured = data.get('is_featured', False)
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            UPDATE courses 
            SET name = %s, description = %s, duration = %s, price = %s, 
                seats = %s, is_featured = %s, updated_at = NOW()
            WHERE id = %s
        """, (name, description, duration, price, seats, is_featured, course_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Delete course
        course_id = request.args.get('id')
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})

# ==================== ORDER MANAGEMENT ====================
@app.route('/admin/orders')
def admin_orders():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    # Get filter parameters
    search = request.args.get('search', '')
    payment_status = request.args.get('payment_status', '')
    delivery_status = request.args.get('delivery_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Build query with filters
    query = """
        SELECT o.*, 
               c.name as customer_name, 
               c.phone as customer_phone, 
               c.email as customer_email, 
               c.address as customer_address,
               p.name as product_name, 
               cs.name as course_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if payment_status:
        query += " AND o.payment_status = %s"
        params.append(payment_status)
    
    if delivery_status:
        query += " AND o.delivery_status = %s"
        params.append(delivery_status)
    
    if start_date:
        query += " AND DATE(o.order_date) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(o.order_date) <= %s"
        params.append(end_date)
    
    query += " ORDER BY o.order_date DESC"
    
    cur.execute(query, params)
    orders = cur.fetchall()
    cur.close()
    
    return render_template('admin/orders.html', 
                         orders=orders,
                         search=search,
                         payment_status=payment_status,
                         delivery_status=delivery_status,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/admin/api/order/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
def api_order(order_id):
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT o.*, c.name as customer_name, c.phone as customer_phone, 
                   c.email as customer_email, c.address as customer_address,
                   p.name as product_name, cs.name as course_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN courses cs ON o.course_id = cs.id
            WHERE o.id = %s
        """, (order_id,))
        order = cur.fetchone()
        cur.close()
        
        if order:
            return jsonify({
                'id': order['id'],
                'customer_id': order['customer_id'],
                'product_id': order['product_id'],
                'course_id': order['course_id'],
                'quantity': order['quantity'],
                'total_price': float(order['total_price']),
                'payment_status': order['payment_status'],
                'delivery_status': order['delivery_status'],
                'order_date': order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order.get('order_date') else None,
                'remarks': order.get('remarks'),
                'customer_name': order['customer_name'],
                'customer_phone': order['customer_phone'],
                'customer_email': order['customer_email'],
                'customer_address': order['customer_address'],
                'product_name': order['product_name'],
                'course_name': order['course_name']
            })
        return jsonify({'error': 'Order not found'}), 404
    
    elif request.method == 'PUT':
        # Update order
        data = request.get_json()
        
        if 'payment_status' in data:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE orders SET payment_status = %s WHERE id = %s", 
                       (data['payment_status'], order_id))
            mysql.connection.commit()
            cur.close()
            
            # Send notification if payment status changed to Paid
            if data['payment_status'] == 'Paid':
                send_payment_notification(order_id)
            
            return jsonify({'success': True})
        
        elif 'delivery_status' in data:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE orders SET delivery_status = %s WHERE id = %s", 
                       (data['delivery_status'], order_id))
            mysql.connection.commit()
            cur.close()
            
            # Send notification if delivery status changed to Delivered
            if data['delivery_status'] == 'Delivered':
                send_delivery_notification(order_id)
            
            return jsonify({'success': True})
        
        elif 'remarks' in data:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE orders SET remarks = %s WHERE id = %s", 
                       (data['remarks'], order_id))
            mysql.connection.commit()
            cur.close()
            return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})

@app.route('/admin/api/orders/export')
def export_orders():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
        SELECT o.id, o.order_date, c.name, c.phone, c.email,
               COALESCE(p.name, cs.name) as item_name,
               o.quantity, o.total_price, o.payment_status, o.delivery_status
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND DATE(o.order_date) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(o.order_date) <= %s"
        params.append(end_date)
    
    cur.execute(query, params)
    orders = cur.fetchall()
    cur.close()
    
    # Create DataFrame
    df = pd.DataFrame(orders, columns=[
        'Order ID', 'Order Date', 'Customer Name', 'Phone', 'Email',
        'Item Name', 'Quantity', 'Total Price', 'Payment Status', 'Delivery Status'
    ])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Orders', index=False)
    
    output.seek(0)
    
    # Return Excel file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'orders_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# ==================== CUSTOMER MANAGEMENT ====================
@app.route('/admin/customers')
def admin_customers():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    search = request.args.get('search', '')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if search:
        cur.execute("""
            SELECT 
                c.*,
                COUNT(o.id) as order_count,
                COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' THEN o.total_price ELSE 0 END), 0) as total_spent
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            WHERE c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("""
            SELECT 
                c.*,
                COUNT(o.id) as order_count,
                COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' THEN o.total_price ELSE 0 END), 0) as total_spent
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
    
    customers = cur.fetchall()
    cur.close()
    
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/api/customer/<int:customer_id>', methods=['GET', 'PUT', 'DELETE'])
def api_customer(customer_id):
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cur.fetchone()
        
        if customer:
            # Get customer's order history
            cur.execute("""
                SELECT o.*, COALESCE(p.name, cs.name) as item_name
                FROM orders o
                LEFT JOIN products p ON o.product_id = p.id
                LEFT JOIN courses cs ON o.course_id = cs.id
                WHERE o.customer_id = %s
                ORDER BY o.order_date DESC
            """, (customer_id,))
            orders = cur.fetchall()
            
            cur.close()
            
            return jsonify({
                'customer': {
                    'id': customer[0],
                    'name': customer[1],
                    'phone': customer[2],
                    'email': customer[3],
                    'address': customer[4],
                    'created_at': customer[5].strftime('%Y-%m-%d %H:%M:%S') if customer[5] else None
                },
                'orders': [{
                    'id': order[0],
                    'item_name': order[10],
                    'quantity': order[4],
                    'total_price': float(order[5]),
                    'payment_status': order[6],
                    'delivery_status': order[7],
                    'order_date': order[8].strftime('%Y-%m-%d %H:%M:%S') if order[8] else None
                } for order in orders]
            })
        cur.close()
        return jsonify({'error': 'Customer not found'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        address = data.get('address')
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            UPDATE customers 
            SET name = %s, phone = %s, email = %s, address = %s
            WHERE id = %s
        """, (name, phone, email, address, customer_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})

# ==================== REPORTS ====================
@app.route('/admin/reports')
def admin_reports():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    report_type = request.args.get('type', 'daily')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Default date range (last 30 days)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get summary statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_price) as total_sales,
            AVG(total_price) as avg_order_value,
            SUM(CASE WHEN payment_status = 'Paid' THEN 1 ELSE 0 END) as paid_orders
        FROM orders 
        WHERE DATE(order_date) BETWEEN %s AND %s
    """, (start_date, end_date))
    stats = cur.fetchone()
    
    # Get sales by day
    cur.execute("""
        SELECT DATE(order_date) as date, SUM(total_price) as daily_sales
        FROM orders 
        WHERE payment_status = 'Paid'
        AND DATE(order_date) BETWEEN %s AND %s
        GROUP BY DATE(order_date)
        ORDER BY date
    """, (start_date, end_date))
    daily_sales = cur.fetchall()
    
    # Get product-wise sales
    cur.execute("""
        SELECT p.name, SUM(o.quantity) as total_quantity, SUM(o.total_price) as total_revenue
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE DATE(o.order_date) BETWEEN %s AND %s
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC
        LIMIT 10
    """, (start_date, end_date))
    product_sales = cur.fetchall()
    
    # Get course-wise sales
    cur.execute("""
        SELECT c.name, SUM(o.quantity) as total_enrollments, SUM(o.total_price) as total_revenue
        FROM orders o
        JOIN courses c ON o.course_id = c.id
        WHERE DATE(o.order_date) BETWEEN %s AND %s
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC
        LIMIT 10
    """, (start_date, end_date))
    course_sales = cur.fetchall()
    
    # Recent orders for detailed report
    cur.execute("""
        SELECT o.*, c.name as customer_name,
               COALESCE(p.name, cs.name) as item_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE DATE(o.order_date) BETWEEN %s AND %s
        ORDER BY o.order_date DESC
        LIMIT 50
    """, (start_date, end_date))
    recent_orders = cur.fetchall()
    
    cur.close()
    
    # Use dictionary keys instead of tuple indices
    total_orders = stats.get('total_orders', 0) or 0
    total_sales = stats.get('total_sales', 0) or 0
    avg_order_value = stats.get('avg_order_value', 0) or 0
    paid_orders = stats.get('paid_orders', 0) or 0
    
    conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
    
    return render_template('admin/reports.html',
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date,
                         total_orders=total_orders,
                         total_sales=total_sales,
                         avg_order_value=avg_order_value,
                         conversion_rate=conversion_rate,
                         daily_sales=daily_sales,
                         product_sales=product_sales,
                         course_sales=course_sales,
                         recent_orders=recent_orders)

@app.route('/admin/api/reports/export')
def export_report():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    report_type = request.args.get('type', 'daily')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Default date range
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if report_type == 'daily':
        cur.execute("""
            SELECT DATE(order_date) as Date, 
                   COUNT(*) as Orders,
                   SUM(total_price) as Revenue,
                   AVG(total_price) as 'Average Order Value'
            FROM orders 
            WHERE DATE(order_date) BETWEEN %s AND %s
            GROUP BY DATE(order_date)
            ORDER BY Date DESC
        """, (start_date, end_date))
        data = cur.fetchall()
        columns = ['Date', 'Orders', 'Revenue', 'Average Order Value']
        filename = f'daily_report_{start_date}_to_{end_date}.xlsx'
        
    elif report_type == 'product':
        cur.execute("""
            SELECT p.name as Product,
                   COUNT(*) as Orders,
                   SUM(o.quantity) as Quantity,
                   SUM(o.total_price) as Revenue
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE DATE(o.order_date) BETWEEN %s AND %s
            GROUP BY p.id, p.name
            ORDER BY Revenue DESC
        """, (start_date, end_date))
        data = cur.fetchall()
        columns = ['Product', 'Orders', 'Quantity', 'Revenue']
        filename = f'product_report_{start_date}_to_{end_date}.xlsx'
        
    elif report_type == 'course':
        cur.execute("""
            SELECT c.name as Course,
                   COUNT(*) as Enrollments,
                   SUM(o.total_price) as Revenue
            FROM orders o
            JOIN courses c ON o.course_id = c.id
            WHERE DATE(o.order_date) BETWEEN %s AND %s
            GROUP BY c.id, c.name
            ORDER BY Revenue DESC
        """, (start_date, end_date))
        data = cur.fetchall()
        columns = ['Course', 'Enrollments', 'Revenue']
        filename = f'course_report_{start_date}_to_{end_date}.xlsx'
    
    cur.close()
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# ==================== BACKUP SYSTEM ====================
@app.route('/admin/backup')
def admin_backup():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM backup_logs ORDER BY backup_date DESC LIMIT 20")
    backups = cur.fetchall()
    cur.close()
    
    return render_template('admin/backup.html', backups=backups)

@app.route('/admin/api/backup', methods=['POST'])
def create_backup():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    backup_type = request.json.get('type', 'manual')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Create backup directory if not exists
        backup_dir = 'database/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Export database tables
        import subprocess
        from app import app
        
        db_config = app.config
        backup_file = f'{backup_dir}/backup_{timestamp}.sql'
        
        # MySQL dump command
        dump_cmd = [
            'mysqldump',
            '-h', db_config['MYSQL_HOST'],
            '-u', db_config['MYSQL_USER'],
            f'-p{db_config["MYSQL_PASSWORD"]}',
            db_config['MYSQL_DB']
        ]
        
        with open(backup_file, 'w') as f:
            subprocess.run(dump_cmd, stdout=f, check=True)
        
        # Log backup in database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO backup_logs (backup_type, file_path, status)
            VALUES (%s, %s, %s)
        """, (backup_type, backup_file, 'success'))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'file': backup_file,
            'timestamp': timestamp
        })
        
    except Exception as e:
        # Log failed backup
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO backup_logs (backup_type, file_path, status)
            VALUES (%s, %s, %s)
        """, (backup_type, '', 'failed'))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': False,
            'message': f'Backup failed: {str(e)}'
        }), 500

@app.route('/admin/api/backup/restore', methods=['POST'])
def restore_backup():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    backup_file = request.json.get('file')
    
    if not os.path.exists(backup_file):
        return jsonify({'error': 'Backup file not found'}), 404
    
    try:
        import subprocess
        from app import app
        
        db_config = app.config
        
        # MySQL restore command
        restore_cmd = [
            'mysql',
            '-h', db_config['MYSQL_HOST'],
            '-u', db_config['MYSQL_USER'],
            f'-p{db_config["MYSQL_PASSWORD"]}',
            db_config['MYSQL_DB']
        ]
        
        with open(backup_file, 'r') as f:
            subprocess.run(restore_cmd, stdin=f, check=True)
        
        return jsonify({
            'success': True,
            'message': 'Database restored successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Restore failed: {str(e)}'
        }), 500

# ==================== HELPER FUNCTIONS ====================
def send_payment_notification(order_id):
    """Send email notification when payment is received"""
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT o.*, c.email, c.name as customer_name,
               COALESCE(p.name, cs.name) as item_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE o.id = %s
    """, (order_id,))
    order = cur.fetchone()
    cur.close()
    
    if not order or not order['email']:
        return False
    
    # Render HTML template
    html_content = render_template('emails/customer_payment.html',
        order_id=order_id,
        customer_name=order['customer_name'],
        item_name=order['item_name'],
        total_price=order['total_price'],
        current_year=datetime.now().year
    )
    
    plain_text = f"""
    Payment Received - Annamalaiyar Software Centre
    
    Dear {order['customer_name']},
    
    Thank you for your payment!
    
    We have successfully received your payment for Order #{order_id}.
    
    Payment Details:
    - Order ID: #{order_id}
    - Item: {order['item_name']}
    - Amount Paid: ₹{order['total_price']}
    - Payment Status: Paid
    
    Your order is now being processed. You will receive another notification when your order is delivered.
    
    If you have any questions, please contact our support team.
    
    Thank you for choosing Annamalaiyar Software Centre!
    """
    
    return send_email(order['email'], f"Payment Received - Order #{order_id}", html_content, plain_text)

def send_delivery_notification(order_id):
    """Send email notification when order is delivered"""
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT o.*, c.email, c.name as customer_name,
               COALESCE(p.name, cs.name) as item_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE o.id = %s
    """, (order_id,))
    order = cur.fetchone()
    cur.close()
    
    if not order or not order['email']:
        return False
    
    # Render HTML template
    html_content = render_template('emails/customer_delivery.html',
        order_id=order_id,
        customer_name=order['customer_name'],
        item_name=order['item_name'],
        delivery_date=datetime.now().strftime('%d-%m-%Y'),
        current_year=datetime.now().year
    )
    
    plain_text = f"""
    Order Delivered - Annamalaiyar Software Centre
    
    Dear {order['customer_name']},
    
    Great news! Your order has been delivered.
    
    We're happy to inform you that your order #{order_id} has been successfully delivered.
    
    Delivery Details:
    - Order ID: #{order_id}
    - Item: {order['item_name']}
    - Delivery Status: Delivered
    - Delivery Date: {datetime.now().strftime('%d-%m-%Y')}
    
    We hope you enjoy your purchase! If you have any issues or need support with your {order['item_name']}, please don't hesitate to contact us.
    
    Thank you for shopping with Annamalaiyar Software Centre. We look forward to serving you again!
    
    Need help? Contact our support team for any assistance.
    """
    
    return send_email(order['email'], f"Order Delivered - #{order_id}", html_content, plain_text)

def send_new_order_notification(order_id):
    """Send email to admin when new order is placed"""
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT o.*, c.name as customer_name, c.phone, c.email, c.address,
               COALESCE(p.name, cs.name) as item_name,
               CASE WHEN o.product_id IS NOT NULL THEN 'Product' ELSE 'Course' END as item_type
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN courses cs ON o.course_id = cs.id
        WHERE o.id = %s
    """, (order_id,))
    order = cur.fetchone()
    cur.close()
    
    if not order:
        return False
    
    # Render HTML template
    html_content = render_template('emails/admin_new_order.html',
        order_id=order_id,
        customer_name=order['customer_name'],
        phone=order['phone'],
        email=order['email'],
        address=order['address'],
        item_type=order['item_type'],
        item_name=order['item_name'],
        quantity=order['quantity'],
        total_price=order['total_price'],
        order_date=order['order_date'].strftime('%d-%m-%Y %H:%M:%S'),
        admin_url='http://localhost:5000/admin/orders',
        current_year=datetime.now().year
    )
    
    plain_text = f"""New Order Received - #{order_id}..."""  # Keep your plain text version
    
    return send_email(EMAIL_CONFIG['admin_email'], f"New Order #{order_id}", html_content, plain_text)

# ==================== AUTO-BACKUP SCHEDULER ====================
def schedule_auto_backup():
    """Schedule automatic backups"""
    # This should be set up as a cron job or scheduled task
    pass

@app.route('/admin/api/backup/download')
def download_backup():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    file_path = request.args.get('file')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Backup file not found'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path),
        mimetype='application/sql'
    )

@app.route('/admin/api/backup/schedule', methods=['POST'])
def schedule_backup():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Store schedule in database or config file
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Implement schedule storage logic here
    
    return jsonify({'success': True, 'message': 'Backup schedule saved'})

if __name__ == '__main__':
    app.run(debug=True)