-- Create Database
CREATE DATABASE IF NOT EXISTS annamalaiyar_db;
USE annamalaiyar_db;

-- Admin Table
CREATE TABLE admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    image_path VARCHAR(500),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Courses Table
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    duration VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    seats INT DEFAULT 0,
    image_path VARCHAR(500),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Customers Table
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Orders Table
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NULL,
    course_id INT NULL,
    quantity INT DEFAULT 1,
    total_price DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Pending','Paid') DEFAULT 'Pending',
    delivery_status ENUM('Pending','Delivered') DEFAULT 'Pending',
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);

-- Add backup log table
CREATE TABLE backup_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    backup_type VARCHAR(50),
    file_path VARCHAR(500),
    backup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20)
);

-- Add email notifications table
CREATE TABLE email_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(100),
    subject VARCHAR(255),
    body TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin (password: admin123)
INSERT INTO admin (username, password_hash) 
VALUES ('admin', '$2b$12$QmzJtj8lB77EJCqAcxq.GeO3samdrT1VLBEVVm1d4b9EMtPkdvXoa');