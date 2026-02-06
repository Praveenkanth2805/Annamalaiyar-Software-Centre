# Annamalaiyar Software Centre
## Software Selling & Teaching Web Application – Technical Specification

---

## 1. Project Overview

**Annamalaiyar Software Centre** is a web-based application designed for:
- Selling **software products**
- Providing **courses / training**
- Managing customers and orders through a secure **admin panel**

Customers **do not require login**.  
Only **admin login** is available and hidden from customers.

---

## 2. Technology Stack

### Frontend
- HTML5
- CSS3 (Material Design style)
- JavaScript (dynamic price calculation, filters, UI interactions)

### Backend
- Python (Flask Framework)

### Database
- MySQL

### Security
- Password hashing with **bcrypt (hashed + salted)**
- Session-based authentication
- Auto logout after inactivity

### Hosting
- PythonAnywhere / Render / Heroku

---

## 3. Application Pages

### 3.1 Customer Pages (No Login)

#### Home Page
- Featured Products
- Featured Courses
- Modern card-based Material UI
- Search and filter support
- Language switch (English / Tamil)

#### Products Page
- List of all products
- Product image, name, price, description
- Select product for order

#### Courses Page
- List of all courses
- Course image, duration, price, description
- Select course for order

#### Order Form
Mandatory fields:
- Name
- Phone
- Email
- Address
- Product / Course selection

Features:
- Live total price calculation
- No online payment
- Order saved as **Pending**
- Confirmation message:
  - “Order placed successfully”

---

## 4. Admin Panel (Secure)

### 4.1 Admin Login
- Separate admin login page
- Not visible to customers
- Hashed + salted password (bcrypt)
- Session-based login
- Auto logout after inactivity

### 4.2 Admin Dashboard
- Total orders
- Pending payments
- Delivered orders
- Daily / Monthly sales summary
- Sales charts

### 4.3 Admin Layout
- Sidebar navigation:
  - Dashboard
  - Products
  - Courses
  - Orders
  - Reports
  - Customers
  - Backup

---

## 5. Admin Features

### 5.1 Products Management
- Add / Edit / Delete products
- Upload product images
- Manage price and stock
- Low stock alert

### 5.2 Courses Management
- Add / Edit / Delete courses
- Upload course images
- Manage duration, price, available seats

### 5.3 Orders Management
- View all orders
- Search and filter by:
  - Customer name
  - Product / Course
  - Payment status
  - Delivery status
  - Date
- Toggle buttons:
  - Payment: Pending / Paid
  - Delivery: Pending / Delivered
- Delete order with confirmation message
- Edit customer details after order

### 5.4 Customer Management
- Maintain full customer list
- View customer purchase history
- Export customer data

### 5.5 Reports
- Daily sales report
- Monthly sales report
- Product-wise sales
- Course-wise sales
- Export reports as CSV / Excel

### 5.6 Backup System
- Manual backup (admin-triggered)
- Automatic backup (daily / weekly)

---

## 6. Database Design

### 6.1 Admin Table
- id (INT, PK, Auto Increment)
- username (VARCHAR)
- password_hash (VARCHAR)
- created_at (DATETIME)

### 6.2 Products Table
- id (INT, PK, Auto Increment)
- name
- description
- price
- stock
- image_path
- created_at
- updated_at

### 6.3 Courses Table
- id (INT, PK, Auto Increment)
- name
- description
- duration
- price
- seats
- image_path
- created_at
- updated_at

### 6.4 Customers Table
- id (INT, PK, Auto Increment)
- name
- phone
- email
- address
- created_at

### 6.5 Orders Table
- id (INT, PK, Auto Increment)
- customer_id (FK)
- product_id (nullable)
- course_id (nullable)
- quantity
- total_price
- payment_status (Pending / Paid)
- delivery_status (Pending / Delivered)
- order_date
- remarks

---

## 7. Order Workflow

1. Customer selects product/course
2. Enters all required details
3. Order stored with:
   - Payment status: Pending
   - Delivery status: Pending
4. Admin delivers product/course
5. Admin marks order as Paid and Delivered

(No online payment integration)

---

## 8. Extra Features

- Email notification to admin when new order is placed
- Live search and filtering
- Responsive design (mobile + desktop)
- Confirmation popups for delete actions
- Featured products and courses

---

## 9. Multi-Language Support (Tamil & English)

### Supported Languages
- English
- Tamil

### Language Selection
- Language switch button: **EN | தமிழ்**
- Default language: English
- Language preference stored using session or cookies

### Customer Side
- Menus
- Product and course labels
- Form fields
- Buttons
- Messages and alerts

Example:
- English: Order placed successfully
- Tamil: ஆர்டர் வெற்றிகரமாக பதிவு செய்யப்பட்டது

### Admin Side
- Login page
- Dashboard labels
- Sidebar menus
- Buttons and status labels

### Translation System
- Language files:
  - `translations/en.json`
  - `translations/ta.json`
- No hard-coded text in HTML
- Flask loads text dynamically

### Database Language Policy
- Data stored in English (default)
- UI text handled via translation files
- No duplicate tables required

---

## 10. Security

- Hashed + salted passwords
- Session protection for admin routes
- Auto logout after inactivity
- Confirmation before delete actions

---

## 11. Future Enhancements

- Online payment integration
- Invoice generation
- WhatsApp notifications
- Multi-admin roles
- Additional language support

---

## 12. Project Status

✅ Requirement gathering completed  
✅ Technical specification finalized  
🚀 Ready for development

---
