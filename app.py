import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3  # ADD THIS IMPORT
import os
from database import *
from pdf_generator import generate_pdf_report, generate_category_pdf_report
import io

# Ensure DB exists when app starts
if not os.path.exists("expense_tracker.db"):
    initialize_database()

# Initialize session state
if 'vat_rate' not in st.session_state:
    st.session_state.vat_rate = 0.15
if 'amount_before_vat' not in st.session_state:
    st.session_state.amount_before_vat = 0.0
if 'vat_amount' not in st.session_state:
    st.session_state.vat_amount = 0.0
if 'total_amount' not in st.session_state:
    st.session_state.total_amount = 0.0
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None
if 'session_expenses' not in st.session_state:
    st.session_state.session_expenses = []
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'vat_amount_display' not in st.session_state:
    st.session_state.vat_amount_display = 0.0
if 'total_amount_display' not in st.session_state:
    st.session_state.total_amount_display = 0.0

def record_expense_page(edit_mode=False):
    st.header("📝 Record New Expense")
    
    # Clear session state button
    if st.button("🧹 Clear All Selections"):
        for key in list(st.session_state.keys()):
            if key not in ['vat_rate', 'current_user', 'session_expenses']:
                del st.session_state[key]
        st.rerun()
    
    # If editing, load the expense data
    if edit_mode and st.session_state.get("edit_id"):
        expense = get_expense_by_id(st.session_state.edit_id)
        if expense:
            # Convert date
            expense_date_val = datetime.strptime(expense['date'], '%Y-%m-%d').date()
            # Set default values for the form
            default_date = expense_date_val
            default_category = get_category_name(expense['category_id'])
            default_subcategory = get_category_name(expense['subcategory_id'])
            default_description = expense['description']
            default_amount = expense['amount_before_vat']
            default_entered_by = expense['entered_by']
        else:
            st.error("Expense not found")
            return
    else:
        # Default values for new expense
        default_date = datetime.today()
        default_category = None
        default_subcategory = None
        default_description = ""
        default_amount = 0.0
        default_entered_by = st.session_state.current_user if st.session_state.current_user else "Hassan Bhatti"
    
    # Main form
    with st.form("expense_form"):
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("Date*", value=default_date)
        with col2:
            employee_names = ["Hassan Bhatti", "Accounts", "Ismail Asas"]
            entered_by = st.selectbox(
                "Entered By (Your Name)*",
                employee_names,
                index=employee_names.index(default_entered_by) if default_entered_by in employee_names else 0
            )
        
        # Category selection
        main_categories = get_categories(level=1)
        main_category = st.selectbox(
            "Main Category*", 
            main_categories,
            index=main_categories.index(default_category) if default_category in main_categories else 0
        )
        
        # Subcategory (only show if main category selected)
        if main_category:
            main_cat_id = get_category_id(main_category)
            subcategories = get_categories(level=2, parent_id=main_cat_id)
            subcategory = st.selectbox(
                "Subcategory",
                [""] + subcategories,
                index=([""] + subcategories).index(default_subcategory) if default_subcategory in subcategories else 0
            )
            
            # Sub-subcategory (only show if subcategory selected)
            if subcategory and subcategory != "":
                subcat_id = get_category_id(subcategory, parent_id=main_cat_id)
                subsubcategories = get_categories(level=3, parent_id=subcat_id)
                if subsubcategories:
                    subsubcategory = st.selectbox(
                        "Sub-Subcategory",
                        [""] + subsubcategories,
                        key='subsubcategory_select'
                    )
                else:
                    subsubcategory = None
            else:
                subsubcategory = None
        else:
            subcategory = None
            subsubcategory = None
        
        # Description
        description = st.text_input("Description*", value=default_description)
        
        # VAT calculation
        st.subheader("VAT Calculation")
        col1, col2 = st.columns(2)
        with col1:
            vat_rate = st.selectbox(
                "VAT Rate*",
                [0.0, 0.15],
                format_func=lambda x: f"{int(x*100)}%",
                index=1
            )
        with col2:
            amount_before_vat = st.number_input(
                "Amount Before VAT (SAR)",
                min_value=0.0,
                format="%.4f",
                value=float(default_amount)
            )
        
        # Calculate VAT
        vat_amount = round(amount_before_vat * vat_rate, 4)
        total_amount = round(amount_before_vat + vat_amount, 4)
        
        # Display calculated amounts
        st.subheader("Calculated Amounts")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "VAT Amount (SAR)",
                value=vat_amount,
                disabled=True,
                format="%.4f"
            )
        with col2:
            st.number_input(
                "Total Amount (SAR)",
                value=total_amount,
                disabled=True,
                format="%.4f"
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Update Expense" if edit_mode else "Submit Expense")
        
        if submitted:
            if not all([entered_by, description, amount_before_vat > 0]):
                st.error("Please fill all required fields (*)")
            else:
                if edit_mode and st.session_state.get("edit_id"):
                    updates = {
                        "date": expense_date.strftime("%Y-%m-%d"),
                        "category_id": get_category_id(main_category),
                        "subcategory_id": get_category_id(subcategory) if subcategory else None,
                        "subsubcategory_id": get_category_id(subsubcategory) if subsubcategory else None,
                        "description": description,
                        "amount_before_vat": amount_before_vat,
                        "vat_amount": vat_amount,
                        "total_amount": total_amount,
                        "entered_by": entered_by
                    }
                    update_expense(st.session_state.edit_id, updates)
                    st.success("✅ Expense updated successfully!")
                    st.session_state.edit_id = None
                    st.rerun()
                else:
                    save_expense(
                        date=expense_date,
                        category=main_category,
                        subcategory=subcategory if subcategory != "" else None,
                        subsubcategory=subsubcategory if subsubcategory else None,
                        subsubsubcategory=None,  # Add if you have this level
                        description=description,
                        amount_before_vat=amount_before_vat,
                        vat_amount=vat_amount,
                        total_amount=total_amount,
                        entered_by=entered_by
                    )
                    st.success("✅ Expense recorded successfully!")
                    st.rerun()

def load_expense_for_editing(expense_id):
    """Simply set the edit ID - the form will handle the rest"""
    st.session_state.edit_id = expense_id
    return True

def employee_view_page():
    st.header("👨‍💼 Employee Expense View")

    if 'current_user' not in st.session_state or not st.session_state.current_user:
        st.session_state.current_user = st.text_input("Enter your name to view your expenses")
        return

    st.subheader(f"Expenses entered by {st.session_state.current_user}")

    # Get expenses for this employee from DB
    expenses = get_expenses_by_user(st.session_state.current_user)
    if expenses.empty:
        st.info("No expenses recorded by you.")
        return

    # Add action column
    action_options = ["Select action", "Edit", "Delete"]
    expenses['action'] = "Select action"

    # Editable table
    edited_df = st.data_editor(
        expenses,
        column_config={
            "action": st.column_config.SelectboxColumn(
                "Action",
                help="Choose what to do with this expense",
                options=action_options,
                required=True,
                width="small"
            )
        },
        disabled=["id", "date", "category", "subcategory", "subsubcategory",
                  "description", "amount_before_vat", "vat_amount", "total_amount", "entered_by"],
        hide_index=True,
        num_rows="fixed",
        key="employee_expenses_editor"
    )

    # Handle actions
    for index, row in edited_df.iterrows():
        if row['action'] == "Delete":
            if st.button(f"🗑️ Confirm Delete #{row['id']}", key=f"confirm_delete_{index}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM expenses WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.success("Expense deleted successfully!")
                st.rerun()

        elif row['action'] == "Edit":
            if st.button(f"✏️ Edit Expense #{row['id']}", key=f"edit_btn_{index}"):
                st.session_state.edit_id = row['id']
                st.session_state.current_page = "Record Expense"
                st.rerun()

    # Download buttons
    st.divider()
    st.subheader("Download Options")

    col1, col2 = st.columns(2)
    with col1:
        # CSV Download
        csv = expenses.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download My Expenses (CSV)",
            csv,
            f"expenses_{st.session_state.current_user}_{datetime.now().date()}.csv",
            "text/csv",
            use_container_width=True
        )
    with col2:
        # PDF Download
        pdf_bytes = generate_pdf_report(
            expenses,
            f"Expenses for {st.session_state.current_user}"
        )
        st.download_button(
            "📥 Download My Expenses (PDF)",
            data=pdf_bytes,
            file_name=f"expenses_{st.session_state.current_user}_{datetime.now().date()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

def manager_view_page():
    st.header("👔 Manager Expense Dashboard")

    # Password protection
    if 'manager_authenticated' not in st.session_state:
        password = st.text_input("Enter manager password", type="password")
        if password == "manager123":
            st.session_state.manager_authenticated = True
            st.rerun()
        elif password:
            st.error("Incorrect password")
        return

    # Database maintenance section
    with st.expander("⚠️ Database Maintenance", expanded=False):
        st.warning("This will permanently delete ALL expenses from the database")
        if st.button("🗑️ Clear All Expenses (Start New Month)"):
            st.session_state.clear_confirmed = True
            st.rerun()

        if st.session_state.get('clear_confirmed'):
            st.error("Are you sure you want to delete ALL expenses? This cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Clear Everything"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM expenses")
                    conn.commit()
                    conn.close()
                    st.success("All expenses have been cleared. Database is now empty.")
                    st.session_state.clear_confirmed = False
                    st.rerun()
            with col2:
                if st.button("❌ No, Cancel"):
                    st.session_state.clear_confirmed = False
                    st.rerun()

    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # Date range filter
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.today())

    # Get filtered expenses
    filtered_expenses = get_expenses(custom_dates=(start_date, end_date))

    if not filtered_expenses.empty:
        # Summary statistics
        st.subheader("Summary Statistics")
        total_expenses = filtered_expenses['total_amount'].sum()
        avg_expense = filtered_expenses['total_amount'].mean()
        num_expenses = len(filtered_expenses)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Expenses", f"SAR {total_expenses:,.4f}")
        col2.metric("Average Expense", f"SAR {avg_expense:,.4f}")
        col3.metric("Number of Expenses", num_expenses)

        # Display all expenses with edit functionality
        st.subheader("All Expense Records")

        display_df = filtered_expenses.copy()
        action_options = ["Select action", "Edit", "Delete"]
        display_df["action"] = "Select action"

        edited_df = st.data_editor(
            display_df,
            column_config={
                "action": st.column_config.SelectboxColumn(
                    "Action",
                    help="Choose to edit or delete",
                    options=action_options,
                    required=True,
                    width="small"
                )
            },
            disabled=["id", "date", "category", "subcategory", "subsubcategory",
                     "amount_before_vat", "vat_amount", "total_amount", "entered_by"],
            hide_index=True,
            use_container_width=True
        )

        # Handle actions
        for index, row in edited_df.iterrows():
            if row["action"] == "Delete":
                if st.button(f"🗑️ Confirm Delete #{row['id']}", key=f"delete_mgr_{index}"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM expenses WHERE id=?", (row["id"],))
                    conn.commit()
                    conn.close()
                    st.success("Expense deleted successfully!")
                    st.rerun()

            elif row["action"] == "Edit":
                if st.button(f"✏️ Edit Expense #{row['id']}", key=f"edit_mgr_{index}"):
                    st.session_state.edit_id = row["id"]
                    st.session_state.current_page = "Record Expense"
                    st.rerun()

        # PDF Download button for all expenses
        pdf_bytes = generate_pdf_report(filtered_expenses, f"Expense Report {start_date} to {end_date}")
        st.download_button(
            "📄 Download All Expenses (PDF)",
            data=pdf_bytes,
            file_name=f"expenses_{start_date}_to_{end_date}.pdf",
            mime="application/pdf"
        )

        # Category breakdown
        st.subheader("Expense Analysis by Category")
        category_summary = get_category_summary(start_date, end_date)

        if not category_summary.empty:
            filtered_summary = category_summary[category_summary['category'] != 'TOTAL']
            st.bar_chart(
                filtered_summary.set_index('category')['total_amount'],
                use_container_width=True
            )

            st.dataframe(category_summary, use_container_width=True)

            pdf_bytes = generate_category_pdf_report(
                category_summary,
                f"Category Summary {start_date} to {end_date}"
            )
            st.download_button(
                "📊 Download Category Summary (PDF)",
                data=pdf_bytes,
                file_name=f"category_summary_{start_date}_to_{end_date}.pdf",
                mime="application/pdf"
            )
    else:
        st.info("No expenses found for the selected date range.")

def main():
    # Initialize database
    initialize_database()

    # Page config
    st.set_page_config(page_title="Expense Tracker", layout="wide")

    # Sidebar navigation
    st.sidebar.title("Navigation")

    # 🔑 Handle edit redirect
    if st.session_state.get("edit_id"):
        record_expense_page(edit_mode=True)
        return

    # Employee login
    if st.sidebar.radio("Login As", ["Employee", "Manager"]) == "Employee":
        page = st.sidebar.radio("Go to", ["Record Expense", "My Expenses"])
        if page == "Record Expense":
            record_expense_page()
        else:
            employee_view_page()
    else:
        # Manager dashboard
        manager_view_page()

if __name__ == "__main__":
    main()