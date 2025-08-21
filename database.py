import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Database configuration
DB_PATH = Path(__file__).parent / "expense_tracker.db"

def initialize_database():
    """Initialize database with tables and default categories if missing"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY,
                 name TEXT NOT NULL,
                 parent_id INTEGER,
                 level INTEGER DEFAULT 1,
                 FOREIGN KEY (parent_id) REFERENCES categories(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY,
                 date TEXT NOT NULL,
                 category_id INTEGER NOT NULL,
                 subcategory_id INTEGER,
                 subsubcategory_id INTEGER,
                 subsubsubcategory_id INTEGER,
                 description TEXT,
                 amount_before_vat REAL NOT NULL,
                 vat_amount REAL NOT NULL,
                 total_amount REAL NOT NULL,
                 entered_by TEXT,
                 FOREIGN KEY (category_id) REFERENCES categories(id),
                 FOREIGN KEY (subcategory_id) REFERENCES categories(id),
                 FOREIGN KEY (subsubcategory_id) REFERENCES categories(id),
                 FOREIGN KEY (subsubsubcategory_id) REFERENCES categories(id))''')
    
    # Only insert default categories if none exist
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        insert_default_categories(conn)
    
    conn.commit()
    conn.close()

def insert_default_categories(conn):
    """Insert default category hierarchy"""
    c = conn.cursor()
    
    # Main Categories
    main_categories = [
        "Food", "Fuel", "Lubricants", "Utilities", 
        "Spare Parts", "Repair & Maintainance", "General Purchases"
    ]
    
    for cat in main_categories:
        c.execute("INSERT INTO categories (name, level) VALUES (?, ?)", (cat, 1))
        
    # Fetch all main category IDs once, after insertion
    c.execute("SELECT id, name FROM categories WHERE level = 1")
    main_cats = {name: id for id, name in c.fetchall()}
    
    # Food Subcategories (level 2)
    food_subs = ["Worker Groceries", "Worker Water", "Worker Tea", 
                "Worker Breakfast", "Worker Lunch", "Worker Dinner"]
    for sub in food_subs:
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                 (sub, main_cats["Food"], 2))
    
    # Fuel Subcategories
    # Petrol (level 2) with its items (level 3)
    c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
             ("Petrol", main_cats["Fuel"], 2))
    petrol_id = c.lastrowid
    petrol_items = ["3818 - Pickup", "8957 - Hyundai", "Workshop"]
    for item in petrol_items:
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                 (item, petrol_id, 3))
    
    # Diesel (level 2) with its subcategories
    c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
             ("Diesel", main_cats["Fuel"], 2))
    diesel_id = c.lastrowid
    
    # Diesel's subcategories (level 3)
    diesel_subs = ["Pickup", "Workshop", "Crane"]
    for sub in diesel_subs:
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                 (sub, diesel_id, 3))
        sub_id = c.lastrowid
        
        # If it's Pickup, add its sub-subcategories (level 4)
        if sub == "Pickup":
            pickup_numbers = ["9431 - Pickup", "8889 - Pickup", "8415 - Pickup"]
            for num in pickup_numbers:
                c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                         (num, sub_id, 4))
    
    # Lubricants Subcategories
    lub_subs = ["Transmission Oil", "Hydrolic Oil", "Gear Oil", "Grease", "Engine Oil"]
    for sub in lub_subs:
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                 (sub, main_cats["Lubricants"], 2))
    
    # Utilities Subcategories
    util_subs = {
        "Phone Bills": ["GM Phone Bill", "Supervisor Phone Bill"],
        "Other": ["Water Bill Workshop", "Water Bill Workers Room", 
                 "Electricity Bill Workshop", "Electricity Bill Workers Room"]
    }
    
    for sub, items in util_subs.items():
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                 (sub, main_cats["Utilities"], 2))
        sub_id = c.lastrowid
        if sub == "Phone Bills":
            for item in items:
                c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                         (item, sub_id, 3))
    
    spare_subcategories = ["Pickup", "Cranes"]  # Level 2
    spare_subsubcategories = ["Batteries", "Filters", "General Spare Parts"]  # Level 3

    for subcategory in spare_subcategories:
        # Insert level 2 category
        c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                (subcategory, main_cats["Spare Parts"], 2))
        subcategory_id = c.lastrowid
        
        # Insert identical level 3 subcategories for both Pickup and Cranes
        for item in spare_subsubcategories:
            c.execute("INSERT INTO categories (name, parent_id, level) VALUES (?, ?, ?)", 
                    (item, subcategory_id, 3))

def get_categories(level=None, parent_id=None):
    conn = get_connection()
    c = conn.cursor()
    
    query = "SELECT id, name FROM categories"
    params = []
    
    if level is not None:
        query += " WHERE level = ?"
        params.append(level)
    
    if parent_id is not None:
        if level is not None:
            query += " AND parent_id = ?"
        else:
            query += " WHERE parent_id = ?"
        params.append(parent_id)
    
    c.execute(query, params)
    categories = [row[1] for row in c.fetchall()]
    conn.close()
    return categories

def get_category_id(name, parent_id=None):
    conn = get_connection()
    c = conn.cursor()
    if parent_id:
        c.execute("SELECT id FROM categories WHERE name = ? AND parent_id = ?", (name, parent_id))
    else:
        c.execute("SELECT id FROM categories WHERE name = ?", (name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_expense(date, category, subcategory, subsubcategory, subsubsubcategory, 
                description, amount_before_vat, vat_amount, total_amount, entered_by):
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Convert date to proper string format
        if hasattr(date, 'strftime'):  # Works for both date and datetime objects
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = str(date)  # Fallback if already string
            
        print(f"DEBUG: Saving expense with date: {date_str}")  # Debug output
        
        # Get category IDs (handles None for subcategories)
        category_id = get_category_id(category)
        subcategory_id = get_category_id(subcategory) if subcategory else None
        subsubcategory_id = get_category_id(subsubcategory) if subsubcategory else None
        subsubsubcategory_id = get_category_id(subsubsubcategory) if subsubsubcategory else None
        
        # Ensure 4-decimal precision for all amounts
        amount_before_vat = round(float(amount_before_vat), 4)
        vat_amount = round(float(vat_amount), 4)
        total_amount = round(float(total_amount), 4)
        
        # Insert the expense
        c.execute('''INSERT INTO expenses 
                    (date, category_id, subcategory_id, subsubcategory_id, subsubsubcategory_id,
                     description, amount_before_vat, vat_amount, total_amount, entered_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (date_str, category_id, subcategory_id, subsubcategory_id, subsubsubcategory_id,
                 description, amount_before_vat, vat_amount, total_amount, entered_by))
        
        conn.commit()
        print(f"DEBUG: Expense saved successfully! Amount: {total_amount:.4f}")  # Confirmation
        
        return c.lastrowid  # Return the ID of the newly created expense
        
    except sqlite3.Error as e:
        print(f"ERROR: Failed to save expense - {str(e)}")
        conn.rollback()
        raise  # Re-raise the error after logging
    except ValueError as e:
        print(f"ERROR: Invalid numeric value - {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()  # Ensure connection always closes

def get_expenses(period=None, custom_dates=None):
    conn = get_connection()
    
    query = '''SELECT e.id, e.date, 
                      c1.name as category, 
                      c2.name as subcategory, 
                      c3.name as subsubcategory,
                      e.description,
                      e.amount_before_vat,
                      e.vat_amount,
                      e.total_amount,
                      e.entered_by
               FROM expenses e
               LEFT JOIN categories c1 ON e.category_id = c1.id
               LEFT JOIN categories c2 ON e.subcategory_id = c2.id
               LEFT JOIN categories c3 ON e.subsubcategory_id = c3.id'''
    
    params = []
    
    if custom_dates:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([custom_dates[0], custom_dates[1]])
    elif period:
        today = datetime.today().date()
        if period == "1st-10th":
            start_date = today.replace(day=1)
            end_date = today.replace(day=10)
        elif period == "11th-20th":
            start_date = today.replace(day=11)
            end_date = today.replace(day=20)
        elif period == "21st-end":
            start_date = today.replace(day=21)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif period == "Current Month":
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        
        if period != "All":
            query += " WHERE date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
    
    query += " ORDER BY date DESC"
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def get_expenses_by_user(username, start_date=None, end_date=None):
    conn = get_connection()
    
    query = '''SELECT e.id, e.date, 
                      c1.name as category, 
                      c2.name as subcategory, 
                      c3.name as subsubcategory,
                      e.description,
                      e.amount_before_vat,
                      e.vat_amount,
                      e.total_amount
               FROM expenses e
               LEFT JOIN categories c1 ON e.category_id = c1.id
               LEFT JOIN categories c2 ON e.subcategory_id = c2.id
               LEFT JOIN categories c3 ON e.subsubcategory_id = c3.id
               WHERE e.entered_by = ?'''
    
    params = [username]
    
    if start_date and end_date:
        query += " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    
    query += " ORDER BY e.date DESC"
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def get_category_summary(start_date=None, end_date=None):
    """Get category summary with optional date filtering"""
    print(f"DEBUG: Running get_category_summary with {start_date} to {end_date}")  # Verification
    
    conn = get_connection()
    
    query = '''
    SELECT 
        c1.name as category,
        c2.name as subcategory,
        SUM(e.total_amount) as total_amount
    FROM expenses e
    JOIN categories c1 ON e.category_id = c1.id
    LEFT JOIN categories c2 ON e.subcategory_id = c2.id
    '''
    
    params = []
    
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start_date.strftime('%Y-%m-%d'), 
                      end_date.strftime('%Y-%m-%d')])
    
    query += ' GROUP BY c1.name, c2.name ORDER BY total_amount DESC'
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        df = pd.concat([df, pd.DataFrame({
            'category': ['TOTAL'],
            'subcategory': [''],
            'total_amount': [df['total_amount'].sum()]
        })], ignore_index=True)
    
    return df

def get_expense_by_id(expense_id):
    """Get complete expense details by ID"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''SELECT e.*, 
                        c1.name as category_name,
                        c2.name as subcategory_name,
                        c3.name as subsubcategory_name
                 FROM expenses e
                 LEFT JOIN categories c1 ON e.category_id = c1.id
                 LEFT JOIN categories c2 ON e.subcategory_id = c2.id
                 LEFT JOIN categories c3 ON e.subsubcategory_id = c3.id
                 WHERE e.id = ?''', (expense_id,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        columns = ['id', 'date', 'category_id', 'subcategory_id', 'subsubcategory_id',
                  'subsubsubcategory_id', 'description', 'amount_before_vat', 'vat_amount', 
                  'total_amount', 'entered_by', 'category_name', 'subcategory_name', 'subsubcategory_name']
        return dict(zip(columns, result))
    return None

def update_expense(expense_id, updates):
    """Update an existing expense with the provided fields"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in ['amount_before_vat', 'vat_amount', 'total_amount']:
                # Ensure 4-decimal precision for amounts
                value = round(float(value), 4)
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(expense_id)
        query = f"UPDATE expenses SET {', '.join(set_clauses)} WHERE id = ?"
        
        c.execute(query, values)
        conn.commit()
        print(f"DEBUG: Expense {expense_id} updated successfully")
        
    except sqlite3.Error as e:
        print(f"ERROR: Failed to update expense {expense_id} - {str(e)}")
        conn.rollback()
        raise
    except ValueError as e:
        print(f"ERROR: Invalid numeric value in update - {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_expenses():
    conn = get_connection()
    query = '''SELECT e.id, e.date, 
                      c1.name as category, 
                      c2.name as subcategory, 
                      c3.name as subsubcategory,
                      e.description,
                      e.amount_before_vat,
                      e.vat_amount,
                      e.total_amount,
                      e.entered_by
               FROM expenses e
               LEFT JOIN categories c1 ON e.category_id = c1.id
               LEFT JOIN categories c2 ON e.subcategory_id = c2.id
               LEFT JOIN categories c3 ON e.subsubcategory_id = c3.id
               ORDER BY e.date DESC'''
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_expenses_pdf():
    """Get all expenses and return as PDF bytes"""
    from pdf_generator import generate_pdf_report
    df = get_all_expenses()
    return generate_pdf_report(df, "All Expense Records")

def get_category_name(category_id):
    """Get category name from ID"""
    if category_id is None:
        return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_connection():
    """Get a database connection"""
    return sqlite3.connect(DB_PATH)

# Initialize database if missing (with verification)
if not DB_PATH.exists():
    print(f"Initializing new database at {DB_PATH}")
    initialize_database()
else:
    print(f"Using existing database at {DB_PATH}")