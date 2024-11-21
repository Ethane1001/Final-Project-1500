from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import uuid
from datetime import date
from flask import session


app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL Database Configuration
db_config = {
    'user': 'root',
    'password': 'Brownie@1001',
    'host': 'localhost',
    'database': 'final_project_new'
}

# Helper function to connect to the database
# Route for User Login
@app.route('/package_login', methods=['GET', 'POST'])
def package_login():
    if request.method == 'POST':
        package_id = request.form['package_id']

        # Establish a database connection
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Check if the package ID exists in the database
                cursor.execute("SELECT package_id FROM package WHERE package_id = %s", (package_id,))
                package = cursor.fetchone()

                if package:
                    # Store package ID in session
                    session['package_id'] = package_id
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))  # Redirect to home page or wherever after login
                else:
                    flash('Invalid Package ID. Please try again.', 'danger')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')

            finally:
                cursor.close()
                connection.close()

    return render_template('package_login.html')

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        flash(f"Database connection error: {err}", 'danger')
        return None

# Route for Home Page
@app.route('/')
def index():
    return render_template('index.html')
# Route to Submit Customer Inquiry
@app.route('/submit_inquiry', methods=['GET', 'POST'])
def submit_inquiry():
    if request.method == 'POST':
        # Retrieve the form data
        customer_id = request.form['customer_id']
        inquiry_info = request.form['inquiry_information']

        # Establish a database connection
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()

                # Insert the new inquiry into the inquiry table
                inquiry_id = str(uuid.uuid4())[:8].upper()
                inquiry_query = """
                    INSERT INTO inquiry (inquiry_id, customer_id, inquiry_information, inquiry_date, inquiry_status)
                    VALUES (%s, %s, %s, %s, 'Pending')
                """
                cursor.execute(inquiry_query, (inquiry_id, customer_id, inquiry_info, date.today()))
                connection.commit()

                flash('Inquiry submitted successfully!', 'success')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')

            finally:
                cursor.close()
                connection.close()

    return render_template('submit_inquiry.html')

# Route to Add Package
# Route to Add Package
@app.route('/add_package', methods=['GET', 'POST'])
def add_package():
    package_id = None
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        address = request.form['address']
        dimensions = request.form['dimensions']
        weight = float(request.form['weight'])
        distance = float(request.form['distance'])

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Check if the customer already exists (using first name, last name, and phone number)
                cursor.execute("""
                    SELECT customer_id FROM customer
                    WHERE first_name = %s AND last_name = %s AND phone_number = %s
                """, (first_name, last_name, phone_number))
                customer = cursor.fetchone()

                # If customer exists, reuse their customer_id
                if customer:
                    customer_id = customer['customer_id']
                else:
                    # Otherwise, create a new customer_id
                    customer_id = str(uuid.uuid4())[:8].upper()

                    # Insert customer
                    customer_query = """
                        INSERT INTO customer (customer_id, first_name, last_name, phone_number, email, address)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(customer_query, (customer_id, first_name, last_name, phone_number, email, address))

                # Create package_id
                package_id = str(uuid.uuid4())[:8].upper()

                # Insert package
                package_query = """
                    INSERT INTO package (package_id, customer_id, status, cost)
                    VALUES (%s, %s, 'Pending', 0)
                """
                cursor.execute(package_query, (package_id, customer_id))

                # Call procedure to calculate total cost
                cursor.callproc('calculate_total_cost', [package_id, weight, dimensions, distance])

                # Update package cost
                cursor.execute("SELECT computed_cost FROM total_cost WHERE package_id = %s", (package_id,))
                cost = cursor.fetchone()['computed_cost']
                update_package_query = "UPDATE package SET cost = %s WHERE package_id = %s"
                cursor.execute(update_package_query, (cost, package_id))

                # Add billing record
                billing_query = """
                    INSERT INTO billing (billing_id, customer_id, package_id, amount_due)
                    VALUES (%s, %s, %s, %s)
                """
                billing_id = str(uuid.uuid4())[:8].upper()
                cursor.execute(billing_query, (billing_id, customer_id, package_id, cost))

                # Add shipping record
                shipping_query = """
                    INSERT INTO shipping (package_obtained_date, package_id)
                    VALUES (%s, %s)
                """
                cursor.execute(shipping_query, (date.today(), package_id))

                connection.commit()
                flash(f"Package created successfully! Your Package ID is {package_id}.", 'success')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')

            finally:
                cursor.close()
                connection.close()

    return render_template('add_package.html', package_id=package_id)

# Route to Track Package
@app.route('/track_package', methods=['GET', 'POST'])
def track_package():
    package_info = None
    if request.method == 'POST':
        package_id = request.form['package_id']

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                query = """
                    SELECT p.package_id, p.status, s.package_obtained_date, s.delivery_date, t.computed_cost
                    FROM package p
                    LEFT JOIN shipping s ON p.package_id = s.package_id
                    LEFT JOIN total_cost t ON p.package_id = t.package_id
                    WHERE p.package_id = %s
                """
                cursor.execute(query, (package_id,))
                package_info = cursor.fetchone()

                if not package_info:
                    flash('No package found with the provided ID.', 'warning')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')

            finally:
                cursor.close()
                connection.close()

    return render_template('track_package.html', package_info=package_info)

# Route to View and Respond to Customer Inquiries
from flask import session

@app.route('/view_inquiries', methods=['GET', 'POST'])
def view_inquiries():
    # Employee login form submission
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')

        # Check if employee ID exists in the database (Example check)
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT employee_id FROM employee_info WHERE employee_id = %s", (employee_id,))
                employee = cursor.fetchone()
                if employee:
                    session['employee_id'] = employee_id
                    flash('Access granted. You can now view inquiries.', 'success')
                else:
                    flash('Invalid Employee ID. Please try again.', 'danger')
            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                connection.close()

    inquiries = None
    # Only fetch inquiries if the employee is logged in
    if 'employee_id' in session:
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT i.inquiry_id, i.inquiry_information, i.inquiry_status, c.first_name, c.last_name
                    FROM inquiry i
                    JOIN customer c ON i.customer_id = c.customer_id
                """
                cursor.execute(query)
                inquiries = cursor.fetchall()
            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                connection.close()

    return render_template('view_inquiries.html', inquiries=inquiries)


# Route to Respond to Inquiry
# Route to Respond to Inquiry
@app.route('/respond_inquiry/<inquiry_id>', methods=['GET', 'POST'])
def respond_inquiry(inquiry_id):
    inquiry_info = None
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        response = request.form['response']

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()

                # Check if the employee exists
                cursor.execute("SELECT employee_id FROM employee_info WHERE employee_id = %s", (employee_id,))
                if not cursor.fetchone():
                    flash('Invalid Employee ID. Please try again.', 'danger')
                    return redirect(url_for('respond_inquiry', inquiry_id=inquiry_id))

                # Update inquiry status
                update_inquiry_query = "UPDATE inquiry SET inquiry_status = 'Resolved' WHERE inquiry_id = %s"
                cursor.execute(update_inquiry_query, (inquiry_id,))

                # Log employee response
                response_query = """
                    INSERT INTO employee_response (employee_id, inquiry_id)
                    VALUES (%s, %s)
                """
                cursor.execute(response_query, (employee_id, inquiry_id))
                connection.commit()

                flash('Inquiry resolved successfully!', 'success')
                return redirect(url_for('view_inquiries'))

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')

            finally:
                cursor.close()
                connection.close()

    # Fetch the inquiry details to display to the user
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT i.inquiry_information, i.inquiry_status, c.first_name, c.last_name
                FROM inquiry i
                JOIN customer c ON i.customer_id = c.customer_id
                WHERE i.inquiry_id = %s
            """
            cursor.execute(query, (inquiry_id,))
            inquiry_info = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('respond_inquiry.html', inquiry_info=inquiry_info, inquiry_id=inquiry_id)

@app.route('/pay_bill', methods=['GET', 'POST'])
def pay_bill():
    if request.method == 'GET':
        package_id = request.args.get('package_id')
        if not package_id:
            return render_template('pay_bill.html')

        # Fetch bills for the given package ID
        connection = get_db_connection()
        bills = None
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT b.billing_id, b.amount_due, b.payment_date, c.first_name, c.last_name
                    FROM billing b
                    JOIN customer c ON b.customer_id = c.customer_id
                    WHERE b.package_id = %s
                """
                cursor.execute(query, (package_id,))
                bills = cursor.fetchall()

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                connection.close()

        return render_template('pay_bill.html', bills=bills, package_id=package_id)

    elif request.method == 'POST':
        # Handle bill payment
        billing_id = request.form.get('billing_id')
        package_id = request.form.get('package_id')

        if not billing_id or not package_id:
            flash('Billing ID or Package ID is missing. Please try again.', 'danger')
            return redirect(url_for('pay_bill'))

        # Process the payment
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()

                # Update payment date in billing
                update_query = """
                    UPDATE billing 
                    SET payment_date = CURDATE() 
                    WHERE billing_id = %s AND package_id = %s
                """
                cursor.execute(update_query, (billing_id, package_id))
                connection.commit()

                if cursor.rowcount > 0:
                    flash('Bill paid successfully!', 'success')
                    return redirect(url_for('index'))  # Redirect to home page after payment
                else:
                    flash('Billing ID not found or not authorized to pay.', 'warning')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                connection.close()

        return redirect(url_for('pay_bill'))



# Run the Flask Application
if __name__ == '__main__':
    app.run(debug=True)
