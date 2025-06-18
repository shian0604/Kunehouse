from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error
import os, json
import logging
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'SECRET123'

logging.basicConfig(level=logging.ERROR)

def get_db_connection():
    try: 
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="E-Commerce"
    )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/enter')
def enter():
    return render_template('index.html')

#BUYER--------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Ensure email and password are provided
        if not email or not password:
            flash('Email and Password are required.', 'error')
            return redirect(url_for('enter'))

        try:
            conn = get_db_connection()
            if conn is None:
                flash('Database connection failed.', 'error')
                return redirect(url_for('enter'))

            cursor = conn.cursor(dictionary=True)

            # Check for buyer in the database
            cursor.execute(
                'SELECT * FROM Buyer_Information WHERE BuyerEmailAddress = %s AND BuyerPassword = %s',
                (email, password)
            )
            buyer = cursor.fetchone()

            if buyer:
                # Set buyer session data
                session['buyer_id'] = buyer['BuyerID']
                session['email'] = buyer['BuyerEmailAddress']

                flash('Login successful. Welcome, Buyer!', 'success')
                return redirect(url_for('buyer_dashboard'))

            # Check for seller in the database
            cursor.execute(
                'SELECT * FROM Seller_Information WHERE SellerEmail = %s AND SellerPassword = %s',
                (email, password)
            )
            seller = cursor.fetchone()

            if seller:
                if seller['ApplicationStatus'] != 'approved':
                    flash('Your application is still under review. Please wait for approval.', 'warning')
                    return redirect(url_for('enter'))

                # Set seller session data
                session['seller_id'] = seller['SellerID']
                session['store_name'] = seller.get('StoreName', 'No Store Name')

                flash('Login successful. Welcome, Seller!', 'success')
                return redirect(url_for('seller_ui'))

            # Check for admin in the database
            cursor.execute(
                'SELECT * FROM admin WHERE AdminEmail = %s AND AdminPassword = %s',
                (email, password)
            )
            admin = cursor.fetchone()

            if admin:
                # Set admin session data
                session['admin_id'] = admin['AdminID']
                session['admin_name'] = admin['AdminName']

                flash('Login successful. Welcome, Admin!', 'success')
                return redirect(url_for('admin_dashboard'))

            # If no matching user found
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('enter'))

        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred during login. Please try again later.', 'error')
            return redirect(url_for('enter'))

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    contacts = request.form['contacts']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Validate password confirmation
    if password != confirm_password:
        flash('Passwords do not match. Please try again.', 'error')
        return redirect(url_for('enter'))

    # Validate password length
    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('enter'))

    # Validate contacts format
    import re
    if not re.match(r"^09\d{2}-\d{3}-\d{4}$", contacts):
        flash('Invalid contact format. Use 09XX-XXX-XXXX.', 'error')
        return redirect(url_for('enter'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if email already exists
        cursor.execute("SELECT * FROM Buyer_Information WHERE BuyerEmailAddress = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('enter'))

        # Insert the new user into the database
        sql = """
            INSERT INTO Buyer_Information (BuyerName, BuyerContact, BuyerEmailAddress, BuyerPassword)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, contacts, email, password))
        conn.commit()

        flash('Successfully registered! Please log in.', 'success')
        return redirect(url_for('enter'))

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred during registration. Please try again later.', 'error')
        return redirect(url_for('enter'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#================================================================================================
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'admin_id' not in session:
        flash('You must be logged in as an admin to access the dashboard.', 'error')
        return redirect(url_for('enter'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch total number of users (assuming users are in admin, buyers, and sellers tables)
        cursor.execute('SELECT COUNT(*) AS total_users FROM admin')
        total_users = cursor.fetchone()['total_users']

        cursor.execute('SELECT COUNT(*) AS total_buyers FROM buyer_information')
        total_buyers = cursor.fetchone()['total_buyers']

        cursor.execute('SELECT COUNT(*) AS total_sellers FROM seller_information')
        total_sellers = cursor.fetchone()['total_sellers']

        # Fetch all admins from the database (optional, if needed)
        cursor.execute('SELECT * FROM admin')
        admins = cursor.fetchall()

        # Pass the total counts to the template
        return render_template('admin_dashboard.html', admins=admins,
                               total_users=total_users, total_buyers=total_buyers, total_sellers=total_sellers)

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching data.', 'error')
        return render_template('admin_dashboard.html', admins=[], total_users=0, total_buyers=0, total_sellers=0)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/add_admin', methods=['POST'])
def add_admin():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')  # Remember to hash the password in production
    contact = request.form.get('contact')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO admin (AdminName, AdminEmail, AdminPassword, AdminContact)
            VALUES (%s, %s, %s, %s)
        ''', (username, email, password, contact))

        conn.commit()
        flash('Admin added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while adding the admin.', 'error')
        return redirect(url_for('admin_dashboard'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/manage_admins', methods=['POST'])
def manage_admins():
    action = request.form.get('action')
    selected_admins = request.form.getlist('selected_admins')

    if not selected_admins:
        flash('No admins selected.', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if action == 'delete':
            cursor.execute('DELETE FROM admin WHERE AdminID IN (%s)' % ','.join(['%s'] * len(selected_admins)), tuple(selected_admins))
            conn.commit()
            flash('Selected admins have been deleted successfully.', 'success')

        elif action == 'edit':
            # Redirect to the edit page with selected admins
            return redirect(url_for('edit_admin', selected_admins=','.join(selected_admins)))

        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while managing admins.', 'error')
        return redirect(url_for('admin_dashboard'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/edit_admin', methods=['GET', 'POST'])
def edit_admin():
    if request.method == 'GET':
        selected_admins = request.args.get('selected_admins', '').split(',')
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute('SELECT * FROM admin WHERE AdminID IN (%s)' % ','.join(['%s'] * len(selected_admins)), tuple(selected_admins))
            admins = cursor.fetchall()

            return render_template('edit_admin.html', admins=admins)

        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while fetching admin data for editing.', 'error')
            return redirect(url_for('admin_dashboard'))

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    elif request.method == 'POST':
        # Update the admin information
        admin_ids = request.form.getlist('admin_id')
        usernames = request.form.getlist('username')
        emails = request.form.getlist('email')
        contacts = request.form.getlist('contact')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            for i in range(len(admin_ids)):
                cursor.execute(
                    """
                    UPDATE admin
                    SET AdminName = %s, AdminEmail = %s, AdminContact = %s
                    WHERE AdminID = %s
                    """,
                    (usernames[i], emails[i], contacts[i], admin_ids[i])
                )

            conn.commit()
            flash('Admins have been updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while updating admin information.', 'error')
            return redirect(url_for('edit_admin'))

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()


@app.route('/manage_users', methods=['GET'])
def manage_users():
    if 'admin_id' not in session:
        flash('You must be logged in as an admin to access this page.', 'error')
        return redirect(url_for('enter'))

    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed.', 'error')
            return redirect(url_for('enter'))

        cursor = conn.cursor(dictionary=True)

        # Fetch all buyers and sellers
        cursor.execute('SELECT * FROM Buyer_Information')
        buyers = cursor.fetchall()

        cursor.execute('SELECT * FROM Seller_Information')
        sellers = cursor.fetchall()

        return render_template('admin_manageusers.html', buyers=buyers, sellers=sellers)

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching data.', 'error')
        return redirect(url_for('enter'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/discard_user', methods=['POST'])
def discard_user():
    if 'admin_id' not in session:
        flash('You must be logged in as an admin to perform this action.', 'error')
        return redirect(url_for('enter'))

    try:
        user_type = request.form.get('user_type')
        selected_ids = request.form.getlist('selected_ids')

        if not selected_ids:
            flash('No users selected for deletion.', 'warning')
            return redirect(url_for('manage_users'))

        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed.', 'error')
            return redirect(url_for('enter'))

        cursor = conn.cursor()

        # Determine the table and ID field based on user type
        if user_type == 'buyer':
            query = 'DELETE FROM Buyer_Information WHERE BuyerID IN (%s)'
        elif user_type == 'seller':
            query = 'DELETE FROM Seller_Information WHERE SellerID IN (%s)'
        else:
            flash('Invalid user type.', 'error')
            return redirect(url_for('manage_users'))

        # Execute deletion for selected IDs
        format_strings = ','.join(['%s'] * len(selected_ids))
        cursor.execute(query % format_strings, selected_ids)
        conn.commit()

        flash(f'Successfully deleted {len(selected_ids)} user(s) from {user_type} table.', 'success')
        return redirect(url_for('manage_users'))

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while deleting users.', 'error')
        return redirect(url_for('manage_users')) 

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/manage_sellers', methods=['GET', 'POST'])
def manage_sellers():
    if 'admin_id' not in session:
        flash('You must be logged in as an admin to manage sellers.', 'error')
        return redirect(url_for('enter'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch all sellers from the database
        cursor.execute('SELECT * FROM Seller_Information')
        sellers = cursor.fetchall()

        if request.method == 'POST':
            action = request.form.get('action')

            # Handle Save Changes
            if action == 'save':
                # Update application statuses for all selected sellers
                for seller in sellers:
                    status_key = f'application_status_{seller["SellerID"]}'
                    new_status = request.form.get(status_key)
                    if new_status:
                        cursor.execute("""
                            UPDATE Seller_Information
                            SET ApplicationStatus = %s
                            WHERE SellerID = %s
                        """, (new_status, seller['SellerID']))
                conn.commit()
                flash('Changes saved successfully.', 'success')

            # Handle Delete Selected
            elif action == 'delete_selected':
                selected_sellers = request.form.getlist('selected_sellers')

                if selected_sellers:
                    # Delete the selected sellers
                    cursor.execute("""
                        DELETE FROM Seller_Information
                        WHERE SellerID IN (%s)
                    """ % ','.join(['%s'] * len(selected_sellers)), tuple(selected_sellers))
                    conn.commit()
                    flash('Selected sellers have been deleted successfully.', 'success')
                else:
                    flash('No sellers selected for deletion.', 'error')

        return render_template('manage_sellers.html', sellers=sellers)

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while managing sellers. Please try again later.', 'error')
        return render_template('manage_sellers.html', sellers=[])

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#================================================================================


@app.route('/buyer_dashboard')
def buyer_dashboard():
    if 'buyer_id' in session:  # Check if the user is logged in
        buyer_id = session['buyer_id']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT BuyerName, BuyerContact, BuyerEmailAddress, BuyerPicture FROM buyer_information WHERE BuyerID = %s", (buyer_id,))
        user = cursor.fetchone()

        # Fetch the buyer's recent searches from the product_search table
        cursor.execute("""
            SELECT DISTINCT SearchInput 
            FROM product_search 
            WHERE BuyerID = %s
            ORDER BY DateAdded DESC
            LIMIT 5
        """, (buyer_id,))
        recent_searches = cursor.fetchall()

        # If there are recent searches, fetch products based on them
        products = []
        if recent_searches:
            # Build a query to search for products related to the recent search inputs
            for search in recent_searches:
                search_input = search['SearchInput']
                cursor.execute("""
                    SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                           p.ProductSize, p.ProductQuantity, p.ProductDescription, p.ProductImg, 
                           s.StoreName, p.ProductColor, p.ProductSubCategory
                    FROM product AS p
                    JOIN seller_information AS s ON p.SellerID = s.SellerID
                    WHERE p.IsActive = TRUE AND p.ProductName LIKE %s
                    ORDER BY p.ProductID DESC
                    LIMIT 25
                """, ('%' + search_input + '%',))
                products += cursor.fetchall()

        # If no recent searches, fetch all active products (fallback)
        if not products:
            cursor.execute("""
                SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                       p.ProductSize, p.ProductQuantity, p.ProductDescription, p.ProductImg, 
                       s.StoreName, p.ProductColor, p.ProductSubCategory
                FROM product AS p
                JOIN seller_information AS s ON p.SellerID = s.SellerID
                WHERE p.IsActive = TRUE
                ORDER BY p.ProductID DESC
                LIMIT 25
            """)
            products = cursor.fetchall()

        if not products:
            flash("No products found.", "warning")
            return redirect(url_for('buyer_dashboard'))

        # Color mapping (optional)
        color_map = {
            'Red': '#B23A48',
            'Blue': '#628ECB',
            'Green': '#aca644',
            'Yellow': '#F9DC5C',
            'Black': '#000000',
            'White': '#FFFFFF'
        }

        # Process each product's sizes and colors
        for product in products:
            # Process sizes
            product['ProductSizes'] = product['ProductSize'].split(',') if product['ProductSize'] else []
            
            # Process colors
            product_colors = product['ProductColor'].split(',') if product['ProductColor'] else []
            cleaned_colors = [color.strip() for color in product_colors]
            product['CustomColors'] = {color: color_map.get(color, '#D3D3D3') for color in cleaned_colors}

        cursor.close()
        conn.close()

        return render_template('m.html', products=products, user=user)  # Render the buyer dashboard page

    else:
        flash('You need to log in to access the dashboard.', 'danger')
        return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_product():
    if 'buyer_id' not in session:
        flash("Please log in to perform a search.", "danger")
        return redirect(url_for('index'))

    buyer_id = session['buyer_id']
    search_input = request.form.get('search', '').strip()
    sort_by = request.form.get('sort_by', '')  # Get the sort option from the form submission

    if not search_input:
        flash("Search input cannot be empty.", "danger")
        return redirect(url_for('buyer_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Base query to fetch products with StoreName included
        query = """ 
            SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                p.ProductSubCategory, p.ProductDescription, p.ProductImg, 
                s.StoreName, s.SellerID, AVG(pr.Rating) AS AverageRating
            FROM product p
            JOIN seller_information s ON p.SellerID = s.SellerID
            LEFT JOIN product_reviews pr ON p.ProductID = pr.ProductID  -- Join with product_reviews to get the rating
            WHERE p.IsActive = 1 AND 
                (p.ProductName LIKE %s OR p.ProductDescription LIKE %s OR p.ProductSubCategory LIKE %s)
            GROUP BY p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                    p.ProductSubCategory, p.ProductDescription, p.ProductImg, 
                    s.StoreName, s.SellerID
        """

        # Parameters for the search input (only 3 placeholders needed)
        search_params = (f"%{search_input}%", f"%{search_input}%", f"%{search_input}%")

        # Add sorting based on the 'sort_by' parameter
        if sort_by == 'a_to_z':
            query += " ORDER BY p.ProductName ASC"
        elif sort_by == 'rate_asc':
            query += " ORDER BY AverageRating ASC"  # Sort by average rating in ascending order
        elif sort_by == 'rate_desc':
            query += " ORDER BY AverageRating DESC"  # Sort by average rating in descending order
        elif sort_by == 'price_asc':
            query += " ORDER BY p.ProductPrice ASC"
        elif sort_by == 'price_desc':
            query += " ORDER BY p.ProductPrice DESC"
        else:
            query += """ ORDER BY 
                            p.ProductSubCategory ASC, s.StoreName ASC, 
                            CASE 
                                WHEN p.ProductName LIKE %s THEN 1
                                WHEN p.ProductSubCategory LIKE %s THEN 2
                                WHEN p.ProductDescription LIKE %s THEN 3
                                ELSE 4
                            END, p.ProductName ASC
                        """
            # Adjust the parameters for the sorting in the else case
            search_params = (f"%{search_input}%", f"%{search_input}%", f"%{search_input}%", 
                             f"{search_input}%", f"{search_input}%", f"{search_input}%")

        # Execute the query with the search term and the sort option
        cursor.execute(query, search_params)
        products = cursor.fetchall()

        if not products:
            flash("No products found for your search.", "info")
            return redirect(url_for('buyer_dashboard'))

        # Log the search in the database
        for product in products:
            cursor.execute(""" 
                INSERT INTO product_search (BuyerID, SellerID, ProductID, SearchInput)
                VALUES (%s, %s, %s, %s)
            """, (buyer_id, product['SellerID'], product['ProductID'], search_input))
        conn.commit()

        # Retrieve recent searches to display similar products in the dashboard
        cursor.execute("""
            SELECT DISTINCT SearchInput
            FROM product_search 
            WHERE BuyerID = %s
            ORDER BY DateAdded DESC
            LIMIT 5
        """, (buyer_id,))
        recent_searches = cursor.fetchall()

        # If there are recent searches, fetch products based on them
        recent_products = []
        if recent_searches:
            for search in recent_searches:
                search_input = search['SearchInput']
                cursor.execute("""
                    SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                           p.ProductSubCategory, p.ProductDescription, p.ProductImg, 
                           s.StoreName, p.ProductColor, p.ProductSubCategory
                    FROM product AS p
                    JOIN seller_information AS s ON p.SellerID = s.SellerID
                    WHERE p.IsActive = TRUE AND p.ProductName LIKE %s
                    ORDER BY p.ProductID DESC
                    LIMIT 5
                """, ('%' + search_input + '%',))
                recent_products += cursor.fetchall()

        cursor.close()
        conn.close()

        # Render the product search page with the products from the search
        return render_template('product_search.html', products=products, search_input=search_input, 
                               sort_by=sort_by, recent_products=recent_products)

    except Exception as e:
        print(f"Error during search: {e}")
        flash("An error occurred while processing your search. Please try again later.", "danger")
        return redirect(url_for('buyer_dashboard'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/buyer_category/<string:category_name>')
def buyer_category(category_name):
    subcategory = request.args.get('subcategory')  # Get subcategory if provided
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Base query to get products
        query = """
            SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, p.ProductSubCategory,
                   p.ProductSize, p.ProductQuantity, p.ProductDescription, p.ProductImg,
                   s.StoreName
            FROM product AS p
            JOIN seller_information AS s ON p.SellerID = s.SellerID
            WHERE p.IsActive = TRUE
        """
        params = []

        # If category is 'all', don't filter by category, but still filter by subcategory if provided
        if category_name != 'all':
            query += " AND p.ProductCategory = %s"
            params.append(category_name)

        # If a subcategory is provided, add it to the query
        if subcategory:
            query += " AND p.ProductSubCategory = %s"
            params.append(subcategory)

        # Order by ProductID
        query += " ORDER BY p.ProductID DESC"

        # Execute query
        cursor.execute(query, tuple(params))
        products = cursor.fetchall()

        # Get available subcategories for the selected category
        subcategories = {
            "all": [
                "Food", "Grooming", "Collars", "Leashes", "Supplements", "Medications", "Vitamins", "First Aid",
                "Chew Toys", "Interactive Toys", "Balls", "Puzzles", "Shirts", "Coats", "Shoes", "Hats",
                "Beds", "Scratch Posts", "Cages", "Playpens", "Aquariums", "Terrariums", "Kennels",
                "Clickers", "Treats", "Training Collars", "Books", "Harnesses", "Carriers", "Travel Bowls", "Backpacks"
            ],
            "pet essentials": ["Food", "Grooming", "Collars", "Leashes"],
            "health and wellness": ["Supplements", "Medications", "Vitamins", "First Aid"],
            "toys": ["Chew Toys", "Interactive Toys", "Balls", "Puzzles"],
            "clothing and accessory": ["Shirts", "Coats", "Shoes", "Hats"],
            "furniture": ["Beds", "Scratch Posts", "Cages", "Playpens"],
            "housing and enclosure": ["Cages", "Aquariums", "Terrariums", "Kennels"],
            "training and behavior": ["Clickers", "Treats", "Training Collars", "Books"],
            "outdoor and activity gear": ["Harnesses", "Carriers", "Travel Bowls", "Backpacks"]
        }

        # Get subcategories for the selected category
        category_subcategories = subcategories.get(category_name, [])

        # If no products are found, add a flash message
        if not products:
            flash("No products found in this category or subcategory.", "info")

    except Exception as e:
        flash("An error occurred while loading products.", "danger")
        products = []
        print(f"Error fetching products: {e}")
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'buyer_category.html',
        products=products,
        category_name=category_name,
        subcategory=subcategory,
        subcategories=category_subcategories
    )



@app.route('/buyer_profile')
def buyer_profile():
    if 'buyer_id' not in session:
        flash('You must be logged in to access your profile.', 'error')
        return redirect(url_for('enter'))

    buyer_id = session['buyer_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Buyer_Information WHERE BuyerID = %s', (buyer_id,))
        user = cursor.fetchone()

        return render_template('buyer_profile.html', user=user)

    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the profile.', 'error')
        return redirect(url_for('enter'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
@app.route('/buyer_edit_profile', methods=['GET'])
def buyer_edit_profile():
    if 'buyer_id' not in session:
        flash("You need to log in to edit your profile.", "danger")
        return redirect(url_for('index'))

    buyer_id = session['buyer_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch buyer information
    cursor.execute("""
        SELECT BuyerName, BuyerContact, BuyerPicture 
        FROM buyer_information 
        WHERE BuyerID = %s
    """, (buyer_id,))
    buyer = cursor.fetchone()

    cursor.close()
    conn.close()

    if not buyer:
        flash("Profile not found.", "danger")
        return redirect(url_for('buyer_dashboard'))

    return render_template('buyer_edit_profile.html', buyer=buyer)

@app.route('/update_buyer_profile', methods=['POST'])
def update_buyer_profile():
    buyer_name = request.form['buyer_name']
    buyer_contact = request.form['buyer_contact']
    profile_picture = request.files.get('profile_picture')

    # Ensure the buyer ID is available in the session
    if 'buyer_id' not in session:
        flash("Please log in to update your profile.", "danger")
        return redirect(url_for('index'))

    buyer_id = session['buyer_id']
    
    # Update the user's profile information in the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if a new profile picture is provided
        if profile_picture and allowed_file(profile_picture.filename):
            # Secure and save the new profile picture
            picture_filename = secure_filename(profile_picture.filename)
            picture_filepath = os.path.join('static/profile', picture_filename)
            profile_picture.save(picture_filepath)

            # Update query with the new profile picture
            cursor.execute("""
                UPDATE buyer_information 
                SET BuyerName = %s, BuyerContact = %s, BuyerPicture = %s
                WHERE BuyerID = %s
            """, (buyer_name, buyer_contact, picture_filename, buyer_id))
        else:
            # No new profile picture, just update name and contact
            cursor.execute("""
                UPDATE buyer_information 
                SET BuyerName = %s, BuyerContact = %s
                WHERE BuyerID = %s
            """, (buyer_name, buyer_contact, buyer_id))

        # Commit the changes
        conn.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash("An error occurred while updating your profile.", "danger")
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('buyer_profile'))


@app.route('/upload_buyer_picture', methods=['POST'])
def upload_buyer_picture():
    if 'buyer_id' not in session:
        flash('You must be logged in as a buyer to upload a profile picture.', 'error')
        return redirect(url_for('buyer_profile'))

    buyer_id = session['buyer_id']

    if 'profile_picture' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('buyer_profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('buyer_profile'))

    if file:
        # Use secure_filename to prevent directory traversal
        filename = secure_filename(file.filename)

        # Save the file in the static/profile folder
        file_path = os.path.join('static/profile', filename)
        file.save(file_path)

        # Only store the filename in the database
        file_path_db = filename

        # Update the database with the new file path
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE Buyer_Information
                SET BuyerPicture = %s
                WHERE BuyerID = %s
            ''', (file_path_db, buyer_id))

            conn.commit()
            flash('Profile picture uploaded successfully!', 'success')

        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while uploading the profile picture.', 'error')

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return redirect(url_for('buyer_profile'))


@app.route('/buyer_orders/<status>')
def buyer_orders(status):
    if 'buyer_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    buyer_id = session['buyer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if status == 'shipped':
            query = """
                SELECT o.OrderID, o.TotalAmount, o.OrderStatus, o.ConfirmationStatus, o.PaymentMethod, 
                       o.ShippingAddress, o.ChosenColor, o.ChosenSize, s.StoreName, p.ProductImg, 
                       p.ProductName, ba.FullAddress, ba.Recipient
                FROM orders o
                JOIN product p ON o.ProductID = p.ProductID
                JOIN seller_information s ON p.SellerID = s.SellerID
                JOIN buyer_address ba ON o.ShippingAddress = ba.AddressID
                WHERE o.BuyerID = %s 
                AND o.OrderStatus IN ('shipped', 'delivered')
                AND p.IsActive = 1
                ORDER BY o.OrderDate DESC
            """
            cursor.execute(query, (buyer_id,))
        else:
            query = """
                SELECT o.OrderID, o.TotalAmount, o.OrderStatus, o.ConfirmationStatus, o.PaymentMethod, 
                       o.ShippingAddress, o.ChosenColor, o.ChosenSize, s.StoreName, p.ProductImg, 
                       p.ProductName, ba.FullAddress, ba.Recipient
                FROM orders o
                JOIN product p ON o.ProductID = p.ProductID
                JOIN seller_information s ON p.SellerID = s.SellerID
                JOIN buyer_address ba ON o.ShippingAddress = ba.AddressID
                WHERE o.BuyerID = %s AND o.OrderStatus = %s
                AND p.IsActive = 1
                ORDER BY o.OrderDate DESC
            """
            cursor.execute(query, (buyer_id, status))

        orders = cursor.fetchall()

        return jsonify({'orders': orders})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching orders.'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



@app.route('/mark_order_received/<int:order_id>', methods=['POST'])
def mark_order_received(order_id):
    if 'buyer_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the OrderStatus to 'review'
        query = "UPDATE orders SET OrderStatus = 'review' WHERE OrderID = %s AND OrderStatus = 'delivered'"
        cursor.execute(query, (order_id,))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Order marked as received successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Order not found or already updated.'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while updating the order status.'})

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



@app.route('/confirm_order/<int:order_id>', methods=['POST'])
def confirm_order(order_id):
    if 'buyer_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the order's ConfirmationStatus to 'approved'
        cursor.execute("""
            UPDATE orders 
            SET ConfirmationStatus = 'approved'
            WHERE OrderID = %s AND BuyerID = %s
        """, (order_id, session['buyer_id']))

        # Update the order_items' ConfirmationStatus to 'approved'
        cursor.execute("""
            UPDATE order_items 
            SET ConfirmationStatus = 'approved'
            WHERE OrderID = %s
        """, (order_id,))

        conn.commit()

        return jsonify({'success': True, 'message': 'Order confirmed successfully.'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while confirming the order.'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'buyer_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete associated rows in order_items first
        cursor.execute("""
            DELETE FROM order_items 
            WHERE OrderID = %s
        """, (order_id,))

        # Then delete the order itself
        cursor.execute("""
            DELETE FROM orders 
            WHERE OrderID = %s AND BuyerID = %s
        """, (order_id, session['buyer_id']))

        conn.commit()
        return jsonify({'success': True, 'message': 'Order canceled successfully.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while canceling the order.'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'review')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Allowed file extensions for review images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/review_product/<int:order_id>', methods=['GET', 'POST'])
def review_product(order_id):
    if 'buyer_id' not in session:
        flash("Please log in to submit a review.", "danger")
        return redirect(url_for('enter'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.OrderID, p.ProductName, p.ProductPrice, o.TotalAmount, o.OrderDate, 
               ba.FullAddress, ba.Recipient, oi.Quantity AS TotalQuantity, 
               o.ChosenColor, o.ChosenSize, s.StoreName, p.ProductImg, p.ProductID
        FROM orders o
        JOIN product p ON o.ProductID = p.ProductID
        JOIN buyer_address ba ON o.ShippingAddress = ba.AddressID
        JOIN order_items oi ON o.OrderID = oi.OrderID
        JOIN seller_information s ON p.SellerID = s.SellerID
        WHERE o.OrderID = %s AND o.BuyerID = %s AND o.OrderStatus = 'review' AND p.IsActive = 1
    """, (order_id, session['buyer_id']))
    
    order_details = cursor.fetchone()

    if not order_details:
        flash("Order not found or cannot be reviewed.", "danger")
        return redirect(url_for('buyer_dashboard'))

    if request.method == 'POST':
        rating = request.form.get('rating')
        review_text = request.form.get('review_text')
        review_image = None

        # Handle image upload if present
        if 'review_image' in request.files:
            image_file = request.files['review_image']
            if image_file and allowed_file(image_file.filename):  # Check if it's an allowed image file type
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(file_path)
                review_image = f"review/{filename}"  # Store relative path in the database

        try:
            # Insert the review into the database, including the image path if present
            cursor.execute("""
                INSERT INTO product_reviews (ProductID, BuyerID, Rating, ReviewText, ReviewImage)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_details['ProductID'], session['buyer_id'], rating, review_text, review_image))
            conn.commit()

            # Update the order status to 'archived' after the review is successfully submitted
            cursor.execute("""
                UPDATE orders
                SET OrderStatus = 'archived'
                WHERE OrderID = %s
            """, (order_id,))
            conn.commit()

            flash("Your review has been submitted, and the order status has been archived.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error submitting review: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('buyer_dashboard'))

    return render_template('product_review.html', order=order_details)



@app.route('/buyer_setting', methods=['GET', 'POST'])
def buyer_setting():
    if 'buyer_id' not in session:
        flash('Please login to access settings', 'warning')
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT BuyerEmailAddress FROM buyer_information WHERE BuyerID = %s', (buyer_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
        else:
            cursor.execute('UPDATE buyer_information SET BuyerPassword = %s WHERE BuyerID = %s', (new_password, buyer_id))
            conn.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('buyer_profile'))

    cursor.close()
    conn.close()

    return render_template('buyer_setting.html', user=user)

@app.route('/buyer/my_address', methods=['GET'])
def my_address():
    buyer_id = session.get('buyer_id')  # Assume buyer_id is stored in the session after login

    if not buyer_id:
        flash('Please log in to view your addresses.', 'error')
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()  # Assume this function connects to your database
        cursor = conn.cursor(dictionary=True)

        # Fetch all addresses for the buyer
        cursor.execute("SELECT * FROM buyer_address WHERE BuyerID = %s", (buyer_id,))
        addresses = cursor.fetchall()

        return render_template('buyer_address.html', addresses=addresses)
    
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"Unexpected error: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return render_template('buyer_address.html', addresses=[])

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/set_default_address', methods=['POST'])
def set_default_address():
    buyer_id = session.get('buyer_id')
    data = request.get_json()
    address_id = data.get('address_id')

    if not buyer_id or not address_id:
        return jsonify({"success": False, "error": "Invalid request."})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Set all addresses to non-default first
        cursor.execute("UPDATE buyer_address SET IsDefault = FALSE WHERE BuyerID = %s", (buyer_id,))
        # Set the selected address as default
        cursor.execute("UPDATE buyer_address SET IsDefault = TRUE WHERE AddressID = %s AND BuyerID = %s", (address_id, buyer_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/buyer/add_address', methods=['GET', 'POST'])
def add_address():
    if request.method == 'POST':
        buyer_id = session.get('buyer_id')
        recipient = request.form.get('recipient').strip()
        phone_number = request.form.get('phone_number').strip()
        full_address = request.form.get('full_address').strip()
        postal_code = request.form.get('postal_code').strip()
        street_name = request.form.get('street_name').strip()
        house_number = request.form.get('house_number').strip()
        is_default = request.form.get('is_default') == 'on'

        conn = get_db_connection()
        cursor = conn.cursor()

        if is_default:
            cursor.execute("UPDATE buyer_address SET IsDefault = FALSE WHERE BuyerID = %s", (buyer_id,))

        cursor.execute("""
            INSERT INTO buyer_address (BuyerID, Recipient, PhoneNumber, FullAddress, 
                                       PostalCode, StreetName, HouseNumber, IsDefault)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (buyer_id, recipient, phone_number, full_address, postal_code, street_name, house_number, is_default))

        conn.commit()
        cursor.close()
        conn.close()

        flash('New address added successfully!', 'success')
        return redirect(url_for('my_address'))

    return render_template('add_address.html')

@app.route('/delete_address', methods=['POST'])
def delete_address():
    buyer_id = session.get('buyer_id')
    data = request.get_json()
    address_id = data.get('address_id')

    if not buyer_id or not address_id:
        return jsonify({"success": False, "error": "Invalid request."})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete the address only if it belongs to the logged-in buyer
        cursor.execute("DELETE FROM buyer_address WHERE AddressID = %s AND BuyerID = %s", (address_id, buyer_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/edit_address/<int:address_id>', methods=['GET'])
def edit_address(address_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM buyer_address WHERE AddressID = %s", (address_id,))
    address = cursor.fetchone()
    cursor.close()
    conn.close()

    if address:
        return render_template('edit_address.html', address=address)
    else:
        return "Address not found", 404

@app.route('/update_address', methods=['POST'])
def update_address():
    address_id = request.form['address_id']
    recipient = request.form['recipient']
    phone_number = request.form['phone_number']
    full_address = request.form['full_address']
    postal_code = request.form['postal_code']
    street_name = request.form['street_name']
    house_number = request.form['house_number']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE buyer_address 
            SET Recipient = %s, PhoneNumber = %s, FullAddress = %s, 
                PostalCode = %s, StreetName = %s, HouseNumber = %s 
            WHERE AddressID = %s
        """, (recipient, phone_number, full_address, postal_code, street_name, house_number, address_id))
        conn.commit()
        return redirect(url_for('my_address'))
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()


@app.route('/buyer_cart')
def buyer_cart():
    if 'buyer_id' not in session:
        flash("Please log in to view your cart.", "danger")
        return redirect(url_for('index'))

    buyer_id = session['buyer_id']
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        if not conn:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('enter'))

        cursor = conn.cursor(dictionary=True)

        # Retrieve cart items, including color and size
        cursor.execute("""
            SELECT bc.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, 
                   p.ProductSubCategory, p.ProductImg, bc.ProductQuantity, 
                   bc.ProductColor, bc.ProductSize
            FROM buyer_cart bc
            JOIN product p ON bc.ProductID = p.ProductID
            WHERE bc.BuyerID = %s AND bc.IsActive = 1
        """, (buyer_id,))
        cart_items = cursor.fetchall()

        total_products = sum(item['ProductQuantity'] for item in cart_items)
        formatted_total = f"{total_products:02}"

    except Exception as e:
        print(f"Error fetching cart items: {e}")
        flash("An error occurred while retrieving your cart. Please try again.", "danger")
        return redirect(url_for('buyer_dashboard'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('buyer_cart.html', cart_items=cart_items, total_products=formatted_total)
 
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'buyer_id' not in session:
        flash("Please log in to add items to your cart.", "danger")
        return redirect(url_for('enter'))

    buyer_id = session['buyer_id']
    product_id = request.form.get('product_id')
    product_color = request.form.get('product_color')
    product_size = request.form.get('product_size')

    try:
        # Retrieve the quantity and validate it
        product_quantity = int(request.form.get('product_quantity', 0))

        if product_quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
    except ValueError as e:
        flash(f"Invalid product quantity: {e}", "warning")
        return redirect(request.referrer)

    if not all([product_id, product_color, product_size, product_quantity > 0]):
        flash("Please select all required options and ensure quantity is greater than 0.", "warning")
        return redirect(request.referrer)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if the product is already in the cart with the same color and size
        cursor.execute("""
            SELECT ProductQuantity FROM buyer_cart
            WHERE BuyerID = %s AND ProductID = %s AND ProductColor = %s AND ProductSize = %s AND IsActive = 1
        """, (buyer_id, product_id, product_color, product_size))
        cart_item = cursor.fetchone()

        if cart_item:
            # Update the quantity if the product is already in the cart
            new_quantity = cart_item['ProductQuantity'] + product_quantity
            cursor.execute("""
                UPDATE buyer_cart
                SET ProductQuantity = %s, DateAdded = NOW()
                WHERE BuyerID = %s AND ProductID = %s AND ProductColor = %s AND ProductSize = %s
            """, (new_quantity, buyer_id, product_id, product_color, product_size))
        else:
            # Add a new product to the cart
            cursor.execute("""
                INSERT INTO buyer_cart (BuyerID, ProductID, ProductQuantity, ProductColor, ProductSize, DateAdded, IsActive)
                VALUES (%s, %s, %s, %s, %s, NOW(), 1)
            """, (buyer_id, product_id, product_quantity, product_color, product_size))

        conn.commit()
        flash("Product added to cart successfully!", "success")

    except Exception as e:
        print(f"Error adding to cart: {e}")
        flash("An error occurred while adding the product to your cart.", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('buyer_dashboard'))


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Query to get product details
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.ProductPrice, p.ProductCategory, p.ProductSubCategory,
                   p.ProductQuantity, p.ProductDescription, p.ProductImg, 
                   s.StoreName, p.ProductSize, p.ProductColor
            FROM product AS p
            JOIN seller_information AS s ON p.SellerID = s.SellerID
            WHERE p.ProductID = %s
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            flash("Product not found.", "warning")
            return redirect(url_for('buyer_dashboard'))

        # Query to get recommended products from the same category, excluding the current product
        cursor.execute("""
            SELECT ProductID, ProductName, ProductPrice, ProductImg 
            FROM product 
            WHERE ProductCategory = %s AND ProductID != %s
            LIMIT 9
        """, (product['ProductCategory'], product_id))
        recommended_products = cursor.fetchall()

        # Query to fetch product reviews along with buyer details
        cursor.execute("""
            SELECT r.ReviewText, r.Rating, r.ReviewImage, r.ReviewDate, b.BuyerName, b.BuyerPicture
            FROM product_reviews AS r
            JOIN buyer_information AS b ON r.BuyerID = b.BuyerID
            WHERE r.ProductID = %s
        """, (product_id,))
        product_reviews = cursor.fetchall()

        cursor.execute("""
        SELECT Rating
        FROM product_reviews
        WHERE ProductID = %s
        """, (product_id,))
        reviews = cursor.fetchall()
        total_reviews = len(reviews)
        ratings_count = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in reviews: 
            ratings_count[review['Rating']] += 1

        average_rating = sum(rating * count for rating, count in ratings_count.items()) / total_reviews if total_reviews > 0 else 0

        # Calculate percentages for progress bars
        ratings_percentage = {
            rating: (count / total_reviews) * 100 if total_reviews > 0 else 0
            for rating, count in ratings_count.items()
        }

        # Extract sizes and colors for the main product
        color_map = {
            'Red': '#B23A48',
            'Blue': '#628ECB',
            'Green': '#aca644',
            'Yellow': '#F9DC5C',
            'Black': '#000000',
            'White': '#FFFFFF'
        }
        product_sizes = product['ProductSize'].split(',') if product['ProductSize'] else []
        product_colors = product['ProductColor'].split(',')
        cleaned_colors = [color.strip() for color in product_colors]
        custom_colors = {color: color_map.get(color, '#D3D3D3') for color in cleaned_colors}

        return render_template(
            'product_detail.html',
            product=product,
            product_sizes=product_sizes,
            custom_colors=custom_colors,
            recommended_products=recommended_products,
            product_reviews=product_reviews,
            average_rating=round(average_rating, 1),
            total_reviews=total_reviews,
            ratings_percentage=ratings_percentage
        )
    except Exception as e:
        print(f"Error: {e}")
        flash("An error occurred while fetching product details.", "danger")
        return redirect(url_for('buyer_dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/buyer_wishlist', methods=['GET', 'POST'])
def buyer_wishlist():
    if 'buyer_id' not in session:
        flash("Please log in to view your wishlist.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Retrieve active wishlist items for the buyer
        cursor.execute("""
            SELECT w.ProductID, w.AddedDate, p.ProductName, p.ProductPrice, p.ProductImg
            FROM buyer_wishlist w
            JOIN product p ON w.ProductID = p.ProductID
            WHERE w.BuyerID = %s AND w.IsActive = TRUE
            ORDER BY w.AddedDate DESC
        """, (buyer_id,))
        wishlist_items = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching wishlist: {e}")
        flash("Unable to load your wishlist. Please try again later.", "danger")
        wishlist_items = []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('buyer_wishlist.html', wishlist_items=wishlist_items)


@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'buyer_id' not in session:
        flash("Please log in to add items to your wishlist.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    product_id = request.form.get('product_id')

    if not product_id:
        flash("Invalid product. Please try again.", "danger")
        return redirect(url_for('buyer_dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the product is already in the wishlist
        cursor.execute("""
            SELECT * FROM buyer_wishlist 
            WHERE BuyerID = %s AND ProductID = %s AND IsActive = TRUE
        """, (buyer_id, product_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            flash("This product is already in your wishlist.", "info")
        else:
            # Insert the product into the wishlist
            cursor.execute("""
                INSERT INTO buyer_wishlist (BuyerID, ProductID) 
                VALUES (%s, %s)
            """, (buyer_id, product_id))
            conn.commit()
            flash("Product added to your wishlist!", "success")

    except Exception as e:
        print(f"Error in add_to_wishlist: {e}")
        flash("An error occurred while adding the product to your wishlist. Please try again.", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('buyer_dashboard'))


@app.route('/remove_from_wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'buyer_id' not in session:
        flash("Please log in to manage your wishlist.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    product_id = request.form.get('product_id')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Soft delete the wishlist entry
        cursor.execute("""
            UPDATE buyer_wishlist
            SET IsActive = FALSE
            WHERE BuyerID = %s AND ProductID = %s
        """, (buyer_id, product_id))
        conn.commit()

        flash("Product removed from your wishlist.", "success")
    except Exception as e:
        print(f"Error removing from wishlist: {e}")
        flash("Unable to remove the product from your wishlist. Please try again.", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('buyer_wishlist'))


#Cart==========================================================================================
@app.route('/place_order', methods=['POST'])
def place_order():
    if 'buyer_id' not in session:
        flash("Please log in to place an order.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if multiple items are being ordered from the cart
        selected_products = request.form.getlist('selected_items')
        if selected_products:
            # Multiple items selected from the cart
            cart_items = []
            for product_id in selected_products:
                cursor.execute("""
                    SELECT bc.ProductID, bc.ProductQuantity, bc.ProductColor, bc.ProductSize, 
                           p.ProductPrice, p.ProductName, p.ProductImg
                    FROM buyer_cart bc
                    JOIN product p ON bc.ProductID = p.ProductID
                    WHERE bc.BuyerID = %s AND bc.ProductID = %s AND bc.IsActive = 1
                """, (buyer_id, product_id))
                item = cursor.fetchone()
                if item:
                    cart_items.append(item)

            if not cart_items:
                flash("No valid items found in your cart. Please try again.", "danger")
                return redirect(url_for('buyer_cart'))

            # Fetch buyer's addresses
            cursor.execute("SELECT * FROM buyer_address WHERE BuyerID = %s", (buyer_id,))
            addresses = cursor.fetchall()

            # Calculate total price for all selected items
            total_price = sum(item['ProductPrice'] * item['ProductQuantity'] for item in cart_items)

            return render_template(
                'order_summary.html',
                cart_items=cart_items,
                total_price=total_price,
                addresses=addresses,
                is_bulk_order=True  # Indicates multiple items
            )

        else:
            # Single product order from product details page
            product_id = request.form.get('product_id')
            product_color = request.form.get('product_color')
            product_size = request.form.get('product_size')
            product_quantity = int(request.form.get('product_quantity'))
            

            # Fetch product details
            cursor.execute("""
                SELECT ProductPrice, ProductName, ProductImg
                FROM product 
                WHERE ProductID = %s
            """, (product_id,))
            product = cursor.fetchone()
            if not product:
                flash("Invalid product. Please try again.", "danger")
                return redirect(url_for('buyer_dashboard'))

            total_price = product['ProductPrice'] * product_quantity;

            # Fetch buyer's addresses
            cursor.execute("SELECT * FROM buyer_address WHERE BuyerID = %s", (buyer_id,))
            addresses = cursor.fetchall()

            return render_template(
                'order_summary.html',
                product=product,
                product_id=product_id,
                product_name=product['ProductName'],
                product_color=product_color,
                product_size=product_size,
                product_quantity=product_quantity,
                total_price=total_price,
                addresses=addresses,
                is_bulk_order=False  # Indicates single item
            )
    except Exception as e:
        print(f"Error in place_order: {e}")
        flash("An error occurred while processing your order. Please try again.", "danger")
        return redirect(url_for('buyer_cart'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/finalize_order', methods=['POST'])
def finalize_order():
    if 'buyer_id' not in session:
        flash("Please log in to complete the order.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    address_id = request.form.get('address_id')
    payment_method = request.form.get('payment_method')
    total_price = request.form.get('total_price')

    if not address_id or not payment_method or not total_price:
        flash("Required information is missing. Please try again.", "danger")
        return redirect(url_for('buyer_cart'))

    try:
        total_price = float(total_price)
    except ValueError:
        flash("Invalid total price. Please try again.", "danger")
        return redirect(url_for('buyer_cart'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        is_bulk_order = request.form.get('is_bulk_order') == 'true'

        if is_bulk_order:
            # Parse bulk order items
            cart_items = []
            try:
                for key in request.form.keys():
                    if key.startswith("products"):
                        item = {
                            "product_id": request.form.get(f"{key}[product_id]"),
                            "ProductQuantity": int(request.form.get(f"{key}[product_quantity]", 0)),
                            "color": request.form.get(f"{key}[color]"),
                            "size": request.form.get(f"{key}[size]"),
                            "price": float(request.form.get(f"{key}[price]", 0)),
                            "seller_id": request.form.get(f"{key}[seller_id]")
                        }
                        cart_items.append(item)
            except Exception as e:
                flash(f"Error parsing cart items: {e}", "danger")
                return redirect(url_for('buyer_cart'))

            if not cart_items:
                flash("No items selected for the order. Please try again.", "danger")
                return redirect(url_for('buyer_cart'))

            for item in cart_items:
                try:
                    # Validate item details
                    product_id = item['product_id']
                    product_quantity = item['ProductQuantity']
                    product_color = item['color']
                    product_size = item['size']
                    product_price = item['price']
                    seller_id = item['seller_id']

                    if not all([product_id, product_quantity, product_color, product_size, product_price, seller_id]):
                        raise ValueError("Missing required product information.")

                    if product_quantity <= 0:
                        raise ValueError(f"Invalid quantity for product {product_id}: must be greater than 0.")

                    total_item_price = product_price * product_quantity;

                    # Insert into orders table
                    cursor.execute("""
                        INSERT INTO orders (
                            BuyerID, ProductID, SellerID, TotalAmount, Quantity, OrderDate, PaymentMethod, 
                            ShippingAddress, OrderStatus, ConfirmationStatus, ChosenColor, ChosenSize, IsActive
                        ) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, 'unpaid', 'pending', %s, %s, TRUE)
                    """, (buyer_id, product_id, seller_id, total_item_price, product_quantity, payment_method, address_id, product_color, product_size))
                    order_id = cursor.lastrowid

                    # Insert into order_items table
                    cursor.execute("""
                        INSERT INTO order_items (
                            OrderID, ProductID, Quantity, Price, TotalPrice, ConfirmationStatus, IsActive
                        ) VALUES (%s, %s, %s, %s, %s, 'pending', TRUE)
                    """, (order_id, product_id, product_quantity, product_price, total_item_price))

                    # Deactivate product in buyer_cart
                    cursor.execute("""
                        UPDATE buyer_cart 
                        SET IsActive = 0 
                        WHERE BuyerID = %s AND ProductID = %s
                    """, (buyer_id, product_id))

                except ValueError as ve:
                    flash(f"Validation error for product {item['product_id']}: {ve}", "danger")
                    conn.rollback()
                    return redirect(url_for('buyer_cart'))
                except Exception as e:
                    flash(f"Database error for product {item['product_id']}: {e}", "danger")
                    conn.rollback()
                    return redirect(url_for('buyer_cart'))

            conn.commit()
            flash("Bulk order placed successfully!", "success")
            return redirect(url_for('buyer_dashboard'))
        
        else:
            product_id = request.form.get('product_id')
            product_quantity = request.form.get('product_quantity')


            product_quantity = int(product_quantity)

            product_color = request.form.get('product_color')
            product_size = request.form.get('product_size')

            # Fetch product details
            cursor.execute("""
                SELECT ProductPrice, SellerID
                FROM product
                WHERE ProductID = %s
            """, (product_id,))
            product = cursor.fetchone()
            if not product:
                flash("Invalid product. Please try again.", "danger")
                return redirect(url_for('buyer_dashboard'))

            seller_id = product['SellerID']
            product_price = product['ProductPrice']
            total_price = product_price * product_quantity;

            # Insert main order record
            cursor.execute("""
                INSERT INTO orders (
                    BuyerID, ProductID, SellerID, TotalAmount, Quantity, OrderDate, PaymentMethod, 
                    ShippingAddress, OrderStatus, ConfirmationStatus, ChosenColor, ChosenSize, IsActive
                ) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, 'unpaid', 'pending', %s, %s, TRUE)
            """, (buyer_id, product_id, seller_id, total_price, product_quantity, payment_method, address_id, product_color, product_size))
            order_id = cursor.lastrowid

            # Insert order item
            cursor.execute("""
                INSERT INTO order_items (OrderID, ProductID, Quantity, Price, TotalPrice, IsActive)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (order_id, product_id, product_quantity, product_price, total_price))

        # Commit the transaction
        conn.commit()
        flash("Order placed successfully!", "success")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error in finalize_order:", str(e))
        flash("There was an error processing your order. Please try again.", "danger")
        return redirect(url_for('buyer_cart'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('buyer_dashboard'))

@app.route('/discard_cart_items', methods=['POST'])
def discard_cart_items():
    if 'buyer_id' not in session:
        flash("Please log in to discard items.", "danger")
        return redirect(url_for('login'))

    buyer_id = session['buyer_id']
    selected_items = request.form.get('selected_items')

    if not selected_items:
        flash("No items selected to discard.", "warning")
        return redirect(url_for('buyer_cart'))

    try:
        selected_items = json.loads(selected_items)  # Parse the JSON string into a Python list

        if not selected_items:
            flash("No items selected to discard.", "warning")
            return redirect(url_for('buyer_cart'))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE buyer_cart
            SET IsActive = 0
            WHERE BuyerID = %s AND ProductID IN (%s)
        """ % (buyer_id, ', '.join(['%s'] * len(selected_items))), tuple(selected_items))

        conn.commit()
        flash("Selected items discarded successfully!", "success")

    except Exception as e:
        print(f"Error discarding items: {e}")
        flash("An error occurred while discarding items. Please try again.", "danger")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('buyer_cart'))


#PRIVACY POLICY==========================================================================
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/cookie_policy')
def cookie_policy():
    return render_template('cookie_policy.html')

@app.route('/accesibility')
def accesibility():
    return render_template('accesibility.html')

@app.route('/ads_info')
def ads_info():
    return render_template('ads_info.html')
#SELLER----------------------------------------------------------------------------------
@app.route('/registration', methods=['POST'])
def seller():
    return render_template('register_seller.html')

@app.route('/add_item', methods=['POST'])
def add_item():
    return render_template('add_item.html')

@app.route('/add_back', methods=['POST'])
def add_back():
    return redirect(url_for('seller_ui'))

@app.route('/seller_signup', methods=['GET', 'POST'])
def seller_registration():
    if request.method == 'POST':
        # Retrieve form inputs
        firstname = request.form.get('firstname').strip()
        lastname = request.form.get('lastname').strip()
        middlename = request.form.get('middleinitial').strip()
        birthday = request.form.get('birthday')
        email = request.form.get('email').strip()
        password = request.form.get('password')

        # Ensure all fields are provided
        if not (firstname and lastname and middlename and birthday and email and password):
            flash('All fields are required for registration.', 'error')
            return render_template('register_seller.html')

        try:
            # Hash password for security
            hashed_password = generate_password_hash(password)

            # Insert seller information into the database
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO Seller_Information 
                (SellerFirstName, SellerLastName, SellerMiddleInitial, SellerBirthDate, SellerEmail, SellerPassword, ApplicationStatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (firstname, lastname, middlename, birthday, email, hashed_password, 'pending')
            cursor.execute(sql, values)
            conn.commit()

            # Store SellerID in session
            session['seller_id'] = cursor.lastrowid

            return redirect(url_for('register_final'))

        except Exception as e:
            print(f"Error during seller registration: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register_seller.html')

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('register_seller.html')

@app.route('/seller_final', methods=['GET', 'POST'])
def register_final():
    if request.method == 'POST':
        # Retrieve form inputs
        storename = request.form.get('storename').strip()
        number = request.form.get('phonenumber').strip()
        bir = request.form.get('bir').strip()
        bank = request.form.get('bankaccount').strip()

        seller_id = session.get('seller_id')

        if not seller_id:
            flash('Session expired. Please start the registration process again.', 'error')
            return redirect(url_for('seller_registration'))

        try:
            # Update seller information in the database
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE Seller_Information 
                SET StoreName = %s, SellerContact = %s, SellerBIR = %s, SellerBankAccount = %s
                WHERE SellerID = %s
            """
            values = (storename, number, bir, bank, seller_id)
            cursor.execute(sql, values)
            conn.commit()

            # Save the store name in the session
            session['store_name'] = storename

            flash('Store details saved successfully. Registration submitted for approval.', 'success')
            return redirect(url_for('buyer_dashboard'))

        except Exception as e:
            print(f"Error during store registration: {e}")
            flash('An error occurred while saving store details. Please try again.', 'error')
            return render_template('register_s.html')

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('register_s.html')

@app.route('/seller_ui')
def seller_ui():
    try:
        # Retrieve the store name and seller ID from the session
        store_name = session.get('store_name', 'No Store Name')
        seller_id = session.get('seller_id')

        if not seller_id:
            flash('Seller ID is missing. Please log in again.', 'error')
            return redirect(url_for('login'))

        products = []
        total_products = 0  # Initialize variable to hold the total product count

        # Connect to the database and retrieve only active products
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)  # Ensure cursor returns results as dictionaries for seller details

            # Fetch seller information
            cursor.execute("""
                SELECT SellerPicture, StoreName, SellerEmail, SellerContact, Banner
                FROM seller_information
                WHERE SellerID = %s
            """, (seller_id,))
            seller = cursor.fetchone()

            # Fetch the total number of active products
            cursor.execute("""
                SELECT COUNT(*) AS total_products
                FROM product 
                WHERE SellerID = %s AND IsActive = TRUE
            """, (seller_id,))
            total_products_data = cursor.fetchone()

            # Ensure total_products is set to 0 if no result is found
            if total_products_data:
                total_products = total_products_data['total_products']
            else:
                total_products = 0

            # Use a different cursor for fetching products to avoid any image path issues
            cursor = conn.cursor()  # Default cursor for product data

            # Retrieve product details
            sql = """
                SELECT ProductID, ProductName, ProductPrice, ProductCategory, ProductSubCategory, 
                       ProductSize, ProductQuantity, ProductDescription, ProductImg
                FROM product 
                WHERE SellerID = %s AND IsActive = TRUE
                LIMIT 15
            """
            cursor.execute(sql, (seller_id,))
            products = cursor.fetchall()

            if not products:
                flash('No active products found for your store.', 'info')

        except Exception as e:
            logging.error(f"Database error: {e}")
            flash('An error occurred while retrieving products. Please try again later.', 'error')
            products = []  # Ensure products is always a list in case of error

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Log the products and total products for debugging
        print("Products:", products)
        print("Total Products Count:", total_products)

    except Exception as e:
        logging.error(f"Error in seller_ui route: {e}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return "An unexpected error occurred.", 500

    return render_template('seller_ui.html', StoreName=store_name, product=products, seller=seller, total_products=total_products)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            # Retrieve and validate form data
            productname = request.form.get('productname').strip()
            productprice = request.form.get('productprice')  # Retrieve price as string
            productcategory = request.form.get('productcategory')
            productsubcategory = request.form.get('subcategory')
            productquantity = request.form.get('productquantity')
            productdescription = request.form.get('productdescription').strip()
            productimage = request.files.get('productimage')
            productsizes = request.form.getlist('productsize')  # List of sizes
            productcolors = request.form.getlist('productcolor')  # List of colors

            # Convert product price to float, with validation
            try:
                productprice = float(productprice)  # Convert to float
                if productprice <= 0:
                    raise ValueError("Product price must be greater than 0.")
            except ValueError:
                flash('Invalid price. Please enter a valid positive number.', 'error')
                return redirect(url_for('add_product'))

            try:
                productquantity = int(productquantity)  # Convert quantity to integer
                if productquantity <= 0:
                    raise ValueError("Quantity must be a positive integer.")
            except ValueError:
                flash('Invalid quantity. Please enter a positive integer.', 'error')
                return redirect(url_for('add_product'))

            # Validate required fields
            if not productname or not productcategory or not productquantity:
                flash('All required fields must be filled out.', 'error')
                return redirect(url_for('add_product'))

            seller_id = session.get('seller_id')
            if not seller_id:
                flash('You must be logged in to add a product.', 'error')
                return redirect(url_for('login'))

            # Check if the product already exists for the same seller
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                check_sql = """
                SELECT * FROM product 
                WHERE ProductName = %s AND SellerID = %s
                """
                cursor.execute(check_sql, (productname, seller_id))
                existing_product = cursor.fetchone()

                if existing_product:
                    flash('A product with the same name already exists. Please choose a different name.', 'error')
                    return redirect(url_for('add_product'))
            except Exception as e:
                logging.error(f"Database error during product check: {e}")
                flash('An error occurred while checking for existing products. Please try again.', 'error')
                return redirect(url_for('add_product'))

            # Handle image upload
            image_path_db = None
            if productimage:
                try:
                    filename = secure_filename(productimage.filename)
                    image_path = os.path.join('static/images', filename)
                    productimage.save(image_path)
                    image_path_db = f"static/images/{filename}"
                except Exception as e:
                    logging.error(f"Error saving image file: {e}")
                    flash('Error uploading the product image. Please try again.', 'error')
                    return redirect(url_for('add_product'))

            # Convert sizes and colors lists to strings
            sizes_str = ", ".join(productsizes)
            colors_str = ", ".join(productcolors)

            # Insert product into the database with IsActive set to true
            try:
                sql = """
                INSERT INTO product 
                (ProductName, ProductPrice, ProductCategory, ProductSubCategory, ProductSize, ProductColor, 
                ProductQuantity, ProductDescription, ProductImg, SellerID, IsActive) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (productname, productprice, productcategory, productsubcategory, sizes_str, colors_str,
                          productquantity, productdescription, image_path_db, seller_id, True)  # IsActive set to True

                cursor.execute(sql, values)
                conn.commit()

            except Exception as e:
                logging.error(f"Database error: {e}")
                flash('An error occurred while adding the product. Please try again.', 'error')
                return redirect(url_for('add_product'))

            finally:
                cursor.close()
                conn.close()

            flash('Product added successfully!', 'success')
            return redirect(url_for('seller_ui'))

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('add_product'))

    return render_template('add_item.html')

    
@app.route('/edit_back', methods=['POST'])
def edit_back():
    return redirect(url_for('seller_products'))

@app.route('/seller_products')
def seller_products():
    seller_id = session.get('seller_id')

    if not seller_id:
        flash('You must be logged in to view your products.', 'error')
        return redirect(url_for('login'))

    products = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary=True to return rows as dictionaries

        

        # Query to retrieve products for the logged-in seller
        sql = """SELECT ProductID, ProductName, ProductPrice, ProductCategory, ProductSubCategory, ProductSize, 
                 ProductQuantity, ProductDescription, ProductImg, IsActive
                 FROM product WHERE SellerID = %s"""
        cursor.execute(sql, (seller_id,))
        products = cursor.fetchall()  # This will now be a list of dictionaries

        if not products:
            flash('No products found. Start by adding a new product!', 'info')

        cursor.execute(""" SELECT SellerPicture, StoreName, SellerEmail, SellerContact, Banner FROM seller_information WHERE SellerID = %s """, (seller_id,))
        seller = cursor.fetchone()

    except Exception as e:
        logging.error(f"Error retrieving products for seller {seller_id}: {e}")
        flash('An error occurred while retrieving your products. Please try again later.', 'error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('seller_products.html', products=products, seller=seller)

@app.route('/archive_product/<int:product_id>', methods=['POST'])
def archive_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Ensure dictionary cursor

        # Check current product status
        cursor.execute("SELECT IsActive FROM product WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()

        if product:
            new_status = not product['IsActive']
            cursor.execute("""
                UPDATE product
                SET IsActive = %s
                WHERE ProductID = %s
            """, (new_status, product_id))
            conn.commit()
            flash(f"Product successfully {'archived' if not new_status else 'unarchived'}.", 'success')
        else:
            flash("Product not found.", 'danger')

    except Exception as e:
        logging.error(f"Error toggling IsActive for product {product_id}: {e}")
        flash(f"An error occurred: {e}", 'danger')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('seller_products'))


@app.route('/manage_stocks', methods=['GET', 'POST'])
def manage_stocks():
    seller_id = session.get('seller_id')

    if not seller_id:
        flash('You must be logged in to manage your stocks.', 'error')
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Enable dictionary mode

        cursor.execute("""
            SELECT SellerPicture, StoreName, SellerEmail, SellerContact, Banner
            FROM seller_information
            WHERE SellerID = %s
        """, (seller_id,))
        seller = cursor.fetchone()

        # Query to retrieve products for the logged-in seller where IsActive is True
        sql = """SELECT ProductID, ProductName, ProductImg, ProductQuantity 
                 FROM product 
                 WHERE SellerID = %s AND IsActive = TRUE"""
        cursor.execute(sql, (seller_id,))
        products = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS total_products
            FROM product
            WHERE SellerID = %s
        """, (seller_id,))
        total_products = cursor.fetchone()['total_products']

    except Exception as e:
        logging.error(f"Error retrieving products for stock management: {e}")
        flash('An error occurred while retrieving your stocks. Please try again later.', 'error')
        seller = None  # Ensure seller is defined if an error occurs
        products = []  # Ensure products is always a list

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('manage_stocks.html', products=products, seller=seller, total_products=total_products)


@app.route('/update_stock', methods=['POST'])
def update_stock():
    """Handles AJAX request to increment or decrement stock."""
    product_id = request.form.get('product_id')
    action = request.form.get('action')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve current quantity
        cursor.execute("SELECT ProductQuantity FROM product WHERE ProductID = %s", (product_id,))
        result = cursor.fetchone()

        if result is None:
            return jsonify({'error': 'Product not found'}), 404

        current_quantity = result[0]

        # Update quantity based on action
        if action == 'increment':
            new_quantity = current_quantity + 1
        elif action == 'decrement' and current_quantity > 0:
            new_quantity = current_quantity - 1
        else:
            new_quantity = current_quantity

        # Update the database
        cursor.execute("UPDATE product SET ProductQuantity = %s WHERE ProductID = %s", (new_quantity, product_id))
        conn.commit()

    except Exception as e:
        logging.error(f"Error updating stock for ProductID {product_id}: {e}")
        return jsonify({'error': 'Failed to update stock'}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify({'new_quantity': new_quantity})

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Validate form input
            try:
                productname = request.form['productname'].strip()
                productprice = float(request.form['productprice'].strip())
                productcategory = request.form['productcategory'].strip()
                productsubcategory = request.form['subcategory'].strip()
                productquantity = int(request.form['productquantity'].strip())
                productsizes = request.form.getlist('productsize')
                productcolors = request.form.getlist('productcolor')
                productdescription = request.form['productdescription'].strip()
                productimage = request.files.get('productimage')

                if not productname or productprice <= 0 or productquantity <= 0:
                    flash('Invalid input. Please check the fields and try again.', 'error')
                    raise ValueError("Invalid input.")
            except ValueError as e:
                logging.error(f"Input validation error: {e}")
                return render_template('edit_product.html', product_id=product_id, error="Invalid input. Please try again.")

            sizes_str = ", ".join(productsizes)
            colors_str = ", ".join(productcolors)

            # Handle image upload
            try:
                if productimage and productimage.filename != '':
                    filename = secure_filename(productimage.filename)
                    image_path = os.path.join('static/images', filename)
                    productimage.save(image_path)
                    image_path_db = f"static/images/{filename}"

                    sql = """
                        UPDATE product
                        SET ProductName = %s, ProductPrice = %s, ProductCategory = %s, 
                            ProductSubCategory = %s, ProductSize = %s, ProductColor = %s,
                            ProductQuantity = %s, ProductDescription = %s, ProductImg = %s
                        WHERE ProductID = %s
                    """
                    cursor.execute(sql, (productname, productprice, productcategory, productsubcategory, sizes_str, colors_str, productquantity, productdescription, image_path_db, product_id))
                else:
                    sql = """
                        UPDATE product
                        SET ProductName = %s, ProductPrice = %s, ProductCategory = %s, 
                            ProductSubCategory = %s, ProductSize = %s, ProductColor = %s,
                            ProductQuantity = %s, ProductDescription = %s
                        WHERE ProductID = %s
                    """
                    cursor.execute(sql, (productname, productprice, productcategory, productsubcategory, sizes_str, colors_str, productquantity, productdescription, product_id))

                conn.commit()
                flash('Product updated successfully!', 'success')
            except Exception as e:
                logging.error(f"Error saving image or updating database: {e}")
                conn.rollback()
                flash('An error occurred while updating the product. Please try again.', 'error')
                return redirect(url_for('edit_product', product_id=product_id))
            finally:
                cursor.close()
                conn.close()

            return redirect(url_for('seller_products'))

        # Fetch current product details for editing
        sql = """SELECT ProductName, ProductPrice, ProductCategory, ProductSubCategory, ProductSize, ProductColor, ProductQuantity, ProductDescription, ProductImg FROM product WHERE ProductID = %s"""
        cursor.execute(sql, (product_id,))
        product = cursor.fetchone()

        if not product:
            cursor.close()
            conn.close()
            flash('Product not found.', 'error')
            return "Product not found", 404

        product_sizes = product[4].split(', ') if product[4] else []
        product_colors = product[5].split(', ') if product[5] else []
    except Exception as e:
        logging.error(f"Error retrieving product details: {e}")
        flash('An error occurred while fetching product details.', 'error')
        return "An error occurred.", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('edit_product.html', product=product, product_sizes=product_sizes, product_colors=product_colors, product_id=product_id)

@app.route('/delete_products', methods=['POST'])
def delete_products():
    data = request.get_json()
    product_ids = data.get('product_ids', [])

    if product_ids:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create placeholders for each product ID
        placeholders = ', '.join(['%s'] * len(product_ids))  # e.g., '%s, %s, %s'
        sql = f"DELETE FROM product WHERE ProductID IN ({placeholders})"

        cursor.execute(sql, product_ids)  # Execute the deletion with the list of IDs

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True), 200

    return jsonify(success=False, message='No product IDs provided.'), 400

@app.route('/sales')
def sales():
    seller_id = session.get('seller_id')
    if not seller_id:
        flash('You must be logged in to view sales reports.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True for JSON-like rows

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total_orders
            FROM orders
            WHERE SellerID = %s
        """, (seller_id,))
        total_orders = cursor.fetchone()['total_orders']

        cursor.execute("""
                SELECT Banner, StoreName
                FROM seller_information
                WHERE SellerID = %s
            """, (seller_id,))
        seller = cursor.fetchone()
        # Query to calculate monthly sales revenue for the seller
        cursor.execute("""
            SELECT DATE_FORMAT(SaleDate, '%Y-%m') AS month,
                   SUM(TotalAmount) AS total_earnings
            FROM sales
            WHERE SellerID = %s
            GROUP BY month
            ORDER BY month DESC
        """, (seller_id,))
        monthly_sales = cursor.fetchall()

        # Query to calculate total revenue grouped by month
        cursor.execute("""
            SELECT DATE_FORMAT(SaleDate, '%Y-%m') AS month,
                   SUM(TotalAmount) AS total_revenue
            FROM sales
            WHERE SellerID = %s
            GROUP BY month
            ORDER BY month DESC
        """, (seller_id,))
        monthly_revenue_grouped = cursor.fetchall()

        # Total revenue across all time (for summary display)
        cursor.execute("""
            SELECT SUM(TotalAmount) AS total_revenue
            FROM sales
            WHERE SellerID = %s
        """, (seller_id,))
        total_revenue = cursor.fetchone()['total_revenue']

        cursor.execute("""
            SELECT p.ProductName, SUM(oi.Quantity) AS total_quantity_sold
            FROM order_items oi
            JOIN orders o ON oi.OrderID = o.OrderID
            JOIN product p ON oi.ProductID = p.ProductID
            WHERE o.SellerID = %s AND oi.IsActive = 1 AND o.IsActive = 1
            GROUP BY p.ProductName
            ORDER BY total_quantity_sold DESC
            LIMIT 1
        """, (seller_id,))
        best_selling_product = cursor.fetchone()

    except Exception as e:
        print(f"Error fetching sales data: {e}")
        flash("An error occurred while fetching sales data.", "danger")
        monthly_sales, monthly_revenue_grouped, total_revenue, best_selling_product, total_orders = [], [], 0, None, 0

    finally:
        cursor.close()
        conn.close()

    return render_template(
        'seller_sales.html',
        monthly_sales=monthly_sales,
        monthly_revenue_grouped=monthly_revenue_grouped,
        total_revenue=total_revenue,
        seller=seller,
        total_orders=total_orders,
        best_selling_product=best_selling_product
    )


def record_sale(seller_id, product_id, quantity_sold, total_amount):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO sales (SellerID, ProductID, QuantitySold, TotalAmount, SaleDate)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, (seller_id, product_id, quantity_sold, total_amount))
        conn.commit()

    except Exception as e:
        print(f"Error recording sale: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/orders', methods=['GET', 'POST'])
def orders():
    seller_id = session.get('seller_id')
    orders = []
    banner = None  # Initialize banner to None

    if seller_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary=True for dictionary-like rows

        try:
            # Fetch the seller's banner
            cursor.execute("""
                SELECT Banner, StoreName
                FROM seller_information
                WHERE SellerID = %s
            """, (seller_id,))
            seller = cursor.fetchone()

            # Fetch orders for the seller, including FullAddress, Recipient, and Quantity, and filtering by ConfirmationStatus = 'approved'
            sql = """
            SELECT o.OrderID, p.ProductImg, p.ProductName, p.ProductPrice, o.OrderStatus, 
                o.TotalAmount, b.BuyerName, o.OrderDate, o.ShippingAddress, o.PaymentMethod,
                ba.FullAddress, ba.Recipient, oi.Quantity
            FROM orders o
            JOIN product p ON o.ProductID = p.ProductID
            JOIN buyer_information b ON o.BuyerID = b.BuyerID
            JOIN buyer_address ba ON o.ShippingAddress = ba.AddressID
            JOIN order_items oi ON o.OrderID = oi.OrderID
            WHERE o.SellerID = %s AND o.ConfirmationStatus = 'approved' AND o.IsActive = TRUE
            """

            cursor.execute(sql, (seller_id,))
            orders = cursor.fetchall()

        except Exception as e:
            print(f"Error fetching orders or banner: {e}")
            flash("An error occurred while fetching your orders.", "error")

        finally:
            cursor.close()
            conn.close()

    return render_template('seller_orders.html', orders=orders, seller=seller)


@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    seller_id = session.get('seller_id')
    if not seller_id:
        flash("You must be logged in to perform this action.", "danger")
        return redirect(url_for('login'))

    new_status = request.form.get('order_status')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True for easier access to rows

    try:
        # Fetch current order details
        cursor.execute("""
            SELECT o.SellerID, o.ProductID, oi.Quantity, o.TotalAmount, o.OrderStatus
            FROM orders o
            JOIN order_items oi ON o.OrderID = oi.OrderID
            WHERE o.OrderID = %s AND o.SellerID = %s
        """, (order_id, seller_id))
        order = cursor.fetchone()

        if not order:
            flash("Order not found or access denied.", "danger")
            return redirect(url_for('orders'))

        # Update the order status
        cursor.execute("""
            UPDATE orders
            SET OrderStatus = %s
            WHERE OrderID = %s AND SellerID = %s
        """, (new_status, order_id, seller_id))

        # Record the sale only if the status changes to 'delivered' or 'archived'
        if new_status in ['delivered', 'archived'] and order['OrderStatus'] not in ['delivered', 'archived']:
            record_sale(
                seller_id=order['SellerID'],
                product_id=order['ProductID'],
                quantity_sold=order['Quantity'],
                total_amount=order['TotalAmount']
            )

        conn.commit()
        flash("Order status updated successfully.", "success")

    except Exception as e:
        conn.rollback()
        print("Error:", e)
        flash("Failed to update order status. Please try again.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('orders'))


@app.route('/archive_order/<int:order_id>', methods=['POST'])
def archive_order(order_id):
    seller_id = session.get('seller_id')
    if not seller_id:
        flash("Please log in to perform this action.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the order belongs to the seller and is eligible for archiving
        cursor.execute("""
            SELECT OrderStatus 
            FROM orders 
            WHERE OrderID = %s AND SellerID = %s
        """, (order_id, seller_id))
        order = cursor.fetchone()

        if not order:
            flash("Order not found or does not belong to you.", "danger")
            return redirect(url_for('orders'))

        # Check if the order's status is one of the allowed statuses
        if order[0] not in ['delivered', 'review', 'archived']:
            flash("Only delivered, review, or archived orders can be archived.", "warning")
            return redirect(url_for('orders'))

        # Archive the order and its items
        cursor.execute("UPDATE orders SET IsActive = 0 WHERE OrderID = %s", (order_id,))
        cursor.execute("UPDATE order_items SET IsActive = 0 WHERE OrderID = %s", (order_id,))
        conn.commit()
        flash("Order archived successfully.", "success")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
        flash("Failed to archive the order. Please try again.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('orders'))


@app.route('/archived_orders', methods=['GET'])
def archived_orders():
    seller_id = session.get('seller_id')
    if not seller_id:
        flash("Please log in to access archived orders.", "danger")
        return redirect(url_for('login'))

    orders = []
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch archived orders
        sql = """
        SELECT o.OrderID, p.ProductImg, p.ProductName, p.ProductPrice, o.OrderStatus, 
               o.TotalAmount, b.BuyerName, o.OrderDate, o.ShippingAddress, o.PaymentMethod,
               ba.FullAddress, ba.Recipient, oi.Quantity
        FROM orders o
        JOIN product p ON o.ProductID = p.ProductID
        JOIN buyer_information b ON o.BuyerID = b.BuyerID
        JOIN buyer_address ba ON o.ShippingAddress = ba.AddressID
        JOIN order_items oi ON o.OrderID = oi.OrderID
        WHERE o.SellerID = %s AND o.IsActive = 0
        """
        cursor.execute(sql, (seller_id,))
        orders = cursor.fetchall()

        sql_count = """
        SELECT COUNT(*) AS total_archived
        FROM orders
        WHERE SellerID = %s AND IsActive = 0
        """
        cursor.execute(sql_count, (seller_id,))
        result = cursor.fetchone()
        total_archived = result['total_archived'] if result else 0

    except Exception as e:
        print("Error:", e)
        flash("Could not fetch archived orders. Please try again.", "danger")
    finally:
        cursor.close()
        conn.close()

    return render_template('seller_archived_orders.html', orders=orders, total_archived=total_archived)


@app.route('/seller_profile')
def seller_profile():
    if 'seller_id' not in session:
        flash('You must be logged in to access your profile.', 'error')
        return redirect(url_for('login'))

    seller_id = session['seller_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch basic seller information
        cursor.execute("""
            SELECT SellerPicture, StoreName, SellerEmail, SellerContact, Banner
            FROM seller_information
            WHERE SellerID = %s
        """, (seller_id,))
        seller = cursor.fetchone()

        # Fetch total number of orders
        cursor.execute("""
            SELECT COUNT(*) AS total_orders
            FROM orders
            WHERE SellerID = %s
        """, (seller_id,))
        total_orders = cursor.fetchone()['total_orders']

        # Fetch total revenue
        cursor.execute("""
            SELECT SUM(TotalAmount) AS total_revenue
            FROM sales
            WHERE SellerID = %s
        """, (seller_id,))
        total_revenue = cursor.fetchone()['total_revenue'] or 0

        # Fetch total products
        cursor.execute("""
            SELECT COUNT(*) AS total_products
            FROM product
            WHERE SellerID = %s
        """, (seller_id,))
        total_products = cursor.fetchone()['total_products']

        return render_template(
            'seller_profile.html',
            seller=seller,
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_products=total_products
        )

    except Exception as e:
        print(f"Error fetching seller profile data: {e}")
        flash('An error occurred while fetching your profile.', 'error')
        return redirect(url_for('login'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/seller_edit_profile', methods=['GET'])
def seller_edit_profile():
    if 'seller_id' not in session:
        flash("You need to log in to edit your profile.", "danger")
        return redirect(url_for('login'))

    seller_id = session['seller_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch seller information
    cursor.execute("""
        SELECT StoreName, SellerContact, SellerPicture, SellerEmail 
        FROM seller_information 
        WHERE SellerID = %s
    """, (seller_id,))
    seller = cursor.fetchone()

    cursor.close()
    conn.close()

    if not seller:
        flash("Profile not found.", "danger")
        return redirect(url_for('seller_dashboard'))

    return render_template('seller_edit_profile.html', seller=seller)

@app.route('/update_seller_profile', methods=['POST'])
def update_seller_profile():
    store_name = request.form['store_name']
    seller_contact = request.form['seller_contact']
    seller_email = request.form['seller_email']
    profile_picture = request.files.get('profile_picture')

    if 'seller_id' not in session:
        flash("Please log in to update your profile.", "danger")
        return redirect(url_for('login'))

    seller_id = session['seller_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if a new profile picture is provided
        if profile_picture and allowed_file(profile_picture.filename):
            picture_filename = secure_filename(profile_picture.filename)
            picture_filepath = os.path.join('static/profile', picture_filename)
            profile_picture.save(picture_filepath)

            # Update query with the new profile picture
            cursor.execute("""
                UPDATE seller_information 
                SET StoreName = %s, SellerContact = %s, SellerPicture = %s, SellerEmail = %s
                WHERE SellerID = %s
            """, (store_name, seller_contact, picture_filename, seller_email, seller_id))
        else:
            # Update only name, contact, and email
            cursor.execute("""
                UPDATE seller_information 
                SET StoreName = %s, SellerContact = %s, SellerEmail = %s
                WHERE SellerID = %s
            """, (store_name, seller_contact, seller_email, seller_id))

        conn.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash("An error occurred while updating your profile.", "danger")
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('seller_profile'))

@app.route('/upload_seller_picture', methods=['POST'])
def upload_seller_picture():
    if 'seller_id' not in session:
        flash('You must be logged in as a seller to upload a profile picture.', 'error')
        return redirect(url_for('seller_profile'))

    seller_id = session['seller_id']

    if 'profile_picture' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('seller_profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('seller_profile'))

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('static/profile', filename)
        file.save(file_path)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE seller_information
                SET SellerPicture = %s
                WHERE SellerID = %s
            """, (filename, seller_id))

            conn.commit()
            flash('Profile picture uploaded successfully!', 'success')
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while uploading the profile picture.', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return redirect(url_for('seller_profile'))

@app.route('/banner_upload', methods=['POST'])
def banner_upload():
    if 'seller_id' not in session:
        flash('You must be logged in as a seller to upload a banner.', 'error')
        return redirect(url_for('seller_profile'))

    seller_id = session['seller_id']

    if 'banner' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('seller_profile'))

    file = request.files['banner']

    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('seller_profile'))

    if file:
        # Secure and save the banner file
        filename = secure_filename(file.filename)
        file_path = os.path.join('static/banners', filename)
        file.save(file_path)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Update the database with the banner path
            cursor.execute("""
                UPDATE seller_information
                SET Banner = %s
                WHERE SellerID = %s
            """, (filename, seller_id))

            conn.commit()
            flash('Banner uploaded successfully!', 'success')
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while uploading the banner.', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return redirect(url_for('seller_profile'))



@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('enter'))  # Redirect to login page

if __name__ == "__main__":
    app.run(debug=True)