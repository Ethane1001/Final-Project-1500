-- Use the appropriate database

USE final_project_new;


-- Drop existing tables to start fresh
DROP TABLE IF EXISTS total_cost;
DROP TABLE IF EXISTS billing;
DROP TABLE IF EXISTS shipping;
DROP TABLE IF EXISTS employee_response;
DROP TABLE IF EXISTS inquiry;
DROP TABLE IF EXISTS employee_info;
DROP TABLE IF EXISTS package;
DROP TABLE IF EXISTS customer;

-- Create the customer table
CREATE TABLE customer(
    `customer_id` VARCHAR(30),
    `first_name` VARCHAR(30),
    `last_name` VARCHAR(30), 
    `phone_number` CHAR(10),
    `email` VARCHAR(30),
    `address` VARCHAR(50),
    CONSTRAINT pk_customer PRIMARY KEY (customer_id)
);

-- Create the employee_info table
CREATE TABLE employee_info(
    `employee_id` VARCHAR(50),
    `first_name` VARCHAR(30),
    `last_name` VARCHAR(30),
    `email` VARCHAR(30),
    CONSTRAINT pk_employee_info PRIMARY KEY (employee_id)
);

-- Create the package table
CREATE TABLE package(
    `package_id` VARCHAR(30),
    `customer_id` VARCHAR(30),
    `status` CHAR(20),
    `cost` DECIMAL(10,2),
    CONSTRAINT fk_package FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT pk_package PRIMARY KEY (package_id)
);

-- Create the inquiry table
CREATE TABLE inquiry(
    `inquiry_id` VARCHAR(30),
    `employee_id` VARCHAR(50),
    `customer_id` VARCHAR(30),
    `inquiry_date` DATE,
    `inquiry_information` VARCHAR(255),
    `inquiry_status` VARCHAR(20),
    CONSTRAINT fk_inquiry_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT fk_inquiry_employee FOREIGN KEY (employee_id) REFERENCES employee_info(employee_id),
    CONSTRAINT pk_inquiry PRIMARY KEY (inquiry_id)
);

-- Create the employee_response table
CREATE TABLE employee_response(
    `employee_id` VARCHAR(50),
    `inquiry_id` VARCHAR(30),
    CONSTRAINT fk_employee_response_employee FOREIGN KEY (employee_id) REFERENCES employee_info(employee_id),
    CONSTRAINT fk_employee_response_inquiry FOREIGN KEY (inquiry_id) REFERENCES inquiry(inquiry_id),
    CONSTRAINT pk_employee_response PRIMARY KEY (employee_id, inquiry_id)
);

-- Create the shipping table
CREATE TABLE shipping(
    `package_obtained_date` DATE,
    `delivery_date` DATE,
    `package_id` VARCHAR(30),
    CONSTRAINT pk_shipping PRIMARY KEY (package_id, package_obtained_date),
    CONSTRAINT fk_shipping FOREIGN KEY (package_id) REFERENCES package(package_id) ON DELETE CASCADE
);

-- Create the billing table
CREATE TABLE billing(
    `billing_id` VARCHAR(30),
    `customer_id` VARCHAR(30),
    `package_id` VARCHAR(30),
    `amount_due` DECIMAL(10,2),
    `payment_date` DATE,
    CONSTRAINT pk_billing PRIMARY KEY (billing_id),
    CONSTRAINT fk_billing_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT fk_billing_package FOREIGN KEY (package_id) REFERENCES package(package_id)
);

-- Create the total_cost table
CREATE TABLE total_cost(
    `cost_id` VARCHAR(30),
    `package_id` VARCHAR(30),
    `weight` DECIMAL(10,2),
    `dimensions` VARCHAR(30),
    `distance` DECIMAL(10,2),
    `computed_cost` DECIMAL(10,2),
    CONSTRAINT pk_total_cost PRIMARY KEY (cost_id),
    CONSTRAINT fk_total_cost FOREIGN KEY (package_id) REFERENCES package(package_id) ON DELETE CASCADE
);

-- Procedure to calculate total cost
DELIMITER $$
CREATE PROCEDURE calculate_total_cost (
    IN pkg_id VARCHAR(30),
    IN weight DECIMAL(10,2),
    IN dimensions VARCHAR(30),
    IN distance DECIMAL(10,2)
)
BEGIN
    DECLARE base_cost DECIMAL(10,2);
    DECLARE dimension_multiplier DECIMAL(10,2);
    DECLARE distance_multiplier DECIMAL(10,2);
    DECLARE total DECIMAL(10,2);
    DECLARE length DECIMAL(10,2);
    DECLARE width DECIMAL(10,2);
    DECLARE height DECIMAL(10,2);
    DECLARE volume DECIMAL(10,2);

    -- Parse dimensions (e.g., "10x5x3")
    SET length = CAST(SUBSTRING_INDEX(dimensions, 'x', 1) AS DECIMAL(10,2));
    SET width = CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(dimensions, 'x', 2), 'x', -1) AS DECIMAL(10,2));
    SET height = CAST(SUBSTRING_INDEX(dimensions, 'x', -1) AS DECIMAL(10,2));
    SET volume = length * width * height;

    -- Define cost components
    SET base_cost = 10.00;
    SET dimension_multiplier = 0.5;
    SET distance_multiplier = 0.1;

    -- Compute total cost
    SET total = base_cost + (weight * 2) + (dimension_multiplier * volume) + (distance * distance_multiplier);

    -- Insert into total_cost table
    INSERT INTO total_cost (cost_id, package_id, weight, dimensions, distance, computed_cost)
    VALUES (UUID(), pkg_id, weight, dimensions, distance, total);
END $$
DELIMITER ;

-- Insert data into customer table
INSERT INTO customer (customer_id, first_name, last_name, phone_number, email, address)
VALUES 
('CUST001', 'John', 'Doe', '1234567890', 'john.doe@example.com', '123 Main St'),
('CUST002', 'Jane', 'Smith', '0987654321', 'jane.smith@example.com', '456 Elm St'),
('CUST003', 'Alice', 'Johnson', '1112223333', 'alice.johnson@example.com', '789 Pine Rd');

-- Insert data into package table
INSERT INTO package (package_id, customer_id, status, cost)
VALUES 
('PKG001', 'CUST001', 'Delivered', 29.99),
('PKG002', 'CUST002', 'In Transit', 49.50),
('PKG003', 'CUST003', 'Pending', 15.75);

-- Insert data into employee_info table
INSERT INTO employee_info (employee_id, first_name, last_name, email)
VALUES 
('EMP001', 'Michael', 'Brown', 'michael.brown@company.com'),
('EMP002', 'Sarah', 'Davis', 'sarah.davis@company.com'),
('EMP003', 'Emily', 'Wilson', 'emily.wilson@company.com');

-- Insert data into inquiry table
INSERT INTO inquiry (inquiry_id, employee_id, customer_id, inquiry_date, inquiry_information, inquiry_status)
VALUES 
('INQ001', 'EMP001', 'CUST001', '2024-11-01', 'Package delayed', 'Resolved'),
('INQ002', 'EMP002', 'CUST002', '2024-11-02', 'Address change request', 'Pending'),
('INQ003', 'EMP003', 'CUST003', '2024-11-03', 'Package lost', 'In Progress');



-- Insert data into employee_response table
INSERT INTO employee_response (employee_id, inquiry_id)
VALUES 
('EMP001', 'INQ001'),
('EMP002', 'INQ002'),
('EMP003', 'INQ003');

-- Insert data into shipping table
INSERT INTO shipping (package_obtained_date, delivery_date, package_id)
VALUES 
('2024-10-20', '2024-10-25', 'PKG001'),
('2024-10-21', NULL, 'PKG002'),
('2024-10-22', NULL, 'PKG003');

-- Insert data into billing table
INSERT INTO billing (billing_id, customer_id, package_id, amount_due, payment_date)
VALUES 
('BILL001', 'CUST001', 'PKG001', 29.99, '2024-10-26'),
('BILL002', 'CUST002', 'PKG002', 49.50, NULL),
('BILL003', 'CUST003', 'PKG003', 15.75, NULL);

-- Call procedure for total cost
CALL calculate_total_cost('PKG001', 5.00, '10x5x3', 100.00);
CALL calculate_total_cost('PKG002', 3.50, '8x4x2', 150.00);
CALL calculate_total_cost('PKG003', 2.00, '12x6x4', 200.00);

-- Show tables
SHOW TABLES;

-- Test queries
SELECT c.first_name, c.last_name, p.package_id, p.status
FROM customer c
JOIN package p ON c.customer_id = p.customer_id;

SELECT * FROM customer;
SELECT * FROM employee_info;
SELECT * FROM package;
SELECT * FROM inquiry;
SELECT * FROM employee_response;
SELECT * FROM shipping;
SELECT * FROM billing;
SELECT * FROM total_cost;

SHOW TABLES;



SELECT * FROM total_cost;




