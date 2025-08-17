import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from database import *
from pdf_generator import generate_pdf_report, generate_category_pdf_report
import io
from database import initialize_database

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

def record_expense_page():
    st.header("📝 Record New Expense")
    
    # Add Clear Selections button at the top
    if st.button("🧹 Clear All Selections"):
        st.session_state.main_category = None
        st.session_state.subcategory = None
        st.session_state.subsubcategory = None
        st.session_state.subsubsubcategory = None
        st.session_state.amount_before_vat_input = 0.0
        st.session_state.vat_amount = 0.0
        st.session_state.total_amount = 0.0
        st.rerun()
    
    # Initialize session state for category tracking
    if 'main_category' not in st.session_state:
        st.session_state.main_category = None
    if 'subcategory' not in st.session_state:
        st.session_state.subcategory = None
    if 'subsubcategory' not in st.session_state:
        st.session_state.subsubcategory = None
    if 'subsubsubcategory' not in st.session_state:
        st.session_state.subsubsubcategory = None
    
    # Store previous selections to detect changes
    prev_main_category = st.session_state.get('main_category')
    
    # Main category selection (outside form)
    main_categories = get_categories(level=1)
    main_category = st.selectbox(
        "Main Category*", 
        main_categories,
        key='main_category_select'
    )
    
    # Detect main category change
    if main_category != prev_main_category:
        st.session_state.main_category = main_category
        st.session_state.subcategory = None
        st.session_state.subsubcategory = None
        st.session_state.subsubsubcategory = None
        st.rerun()
    
    # Subcategory selection (only show if main category is selected)
    if st.session_state.main_category:
        main_cat_id = get_category_id(st.session_state.main_category)
        subcategories = get_categories(level=2, parent_id=main_cat_id)

        prev_subcategory = st.session_state.get('subcategory')
        subcategory = st.selectbox(
            "Subcategory",
            [""] + subcategories,
            key='subcategory_select'
        )

        # Detect subcategory change
        if subcategory != prev_subcategory:
            st.session_state.subcategory = subcategory
            st.session_state.subsubcategory = None
            st.session_state.subsubsubcategory = None
            st.rerun()

        # Sub-subcategory selection (only show if subcategory is selected)
        if st.session_state.subcategory and st.session_state.subcategory != "":
            subcat_id = get_category_id(st.session_state.subcategory, parent_id=main_cat_id)
            subsubcategories = get_categories(level=3, parent_id=subcat_id)

            if subsubcategories:  # Only show if subsubcategories exist
                prev_subsubcategory = st.session_state.get('subsubcategory')
                subsubcategory = st.selectbox(
                    "Sub-Subcategory",
                    [""] + subsubcategories,
                    key='subsubcategory_select'
                )

                # Detect subsubcategory change
                if subsubcategory != prev_subsubcategory:
                    st.session_state.subsubcategory = subsubcategory
                    st.rerun()

                # Sub-sub-subcategory selection
                if st.session_state.subsubcategory and st.session_state.subsubcategory != "":
                    subsubcat_id = get_category_id(st.session_state.subsubcategory, parent_id=subcat_id)
                    subsubsubcategories = get_categories(level=4, parent_id=subsubcat_id)

                    if subsubsubcategories:
                        subsubsubcategory = st.selectbox(
                            "Sub-Sub-Subcategory",
                            [""] + subsubsubcategories,
                            key='subsubsubcategory_select'
                        )
                    else:
                        subsubsubcategory = None
                else:
                    subsubsubcategory = None
            else:
                subsubcategory = None
                subsubsubcategory = None
        else:
            subsubcategory = None
            subsubsubcategory = None
    else:
        subcategory = None
        subsubcategory = None
        subsubsubcategory = None
        
    # VAT calculation section (outside form)
    st.subheader("VAT Calculation")
    col1, col2 = st.columns(2)
    with col1:
        vat_rate = st.selectbox(
            "VAT Rate*",
            [0.0, 0.15],
            format_func=lambda x: f"{int(x*100)}%",
            index=1,  # Default to 15%
            key='vat_rate_select'
        )
    with col2:
        amount_before_vat = st.number_input(
            "Amount Before VAT (SAR)",
            min_value=0.0, 
            format="%.2f",
            key='amount_before_vat_input'
        )
    
    # Calculate button (outside form)
    if st.button("Calculate VAT"):
        if amount_before_vat <= 0:
            st.error("Amount must be positive")
        else:
            st.session_state.vat_amount = round(amount_before_vat * vat_rate, 2)
            st.session_state.total_amount = round(amount_before_vat + st.session_state.vat_amount, 2)
            st.rerun()
    
    # Display calculated values (outside form)
    st.subheader("Calculated Amounts")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input(
            "VAT Amount (SAR)",
            value=st.session_state.get('vat_amount', 0.0), 
            disabled=True,
            key='vat_amount_display'
        )
    with col2:
        st.number_input(
            "Total Amount (SAR)",
            value=st.session_state.get('total_amount', 0.0), 
            disabled=True,
            key='total_amount_display'
        )
    
    # Expense details form
    with st.form("expense_form", clear_on_submit=True):
        # Date input
        expense_date = st.date_input("Date*", datetime.today())
        
        # Employee name
        entered_by = st.text_input("Entered By (Your Name)*", key='entered_by_input')
        
        # Expense details
        description = st.text_input("Description*", key='description_input')
        
        submitted = st.form_submit_button("Submit Expense")
        
        if submitted:
            if not all([entered_by, description, amount_before_vat > 0]):
                st.error("Please fill all required fields (*)")
            elif st.session_state.vat_amount is None or st.session_state.total_amount is None:
                st.error("Please calculate VAT before submitting")
            else:
                save_expense(
                    date=expense_date,
                    category=st.session_state.main_category,
                    subcategory=st.session_state.subcategory if st.session_state.subcategory != "" else None,
                    subsubcategory=st.session_state.subsubcategory if st.session_state.subsubcategory and st.session_state.subsubcategory != "" else None,
                    subsubsubcategory=subsubsubcategory if subsubsubcategory and subsubsubcategory != "" else None,
                    description=description,
                    amount_before_vat=amount_before_vat,
                    vat_amount=st.session_state.vat_amount,
                    total_amount=st.session_state.total_amount,
                    entered_by=entered_by
                )
                
                # Show detailed success message
                st.success(f"""
                ✅ Expense recorded successfully!
                
                **Details:**
                - Date: {expense_date.strftime('%Y-%m-%d')}
                - Category: {st.session_state.main_category}
                - Subcategory: {st.session_state.subcategory if st.session_state.subcategory else 'N/A'}
                - Sub-subcategory: {st.session_state.subsubcategory if st.session_state.subsubcategory else 'N/A'}
                - Amount: SAR {st.session_state.total_amount:,.2f}
                - Entered by: {entered_by}
                """)
                
                # Also add to session expenses
                expense_record = {
                    "date": expense_date.strftime("%Y-%m-%d"),
                    "category": st.session_state.main_category,
                    "subcategory": st.session_state.subcategory if st.session_state.subcategory != "" else None,
                    "subsubcategory": st.session_state.subsubcategory if st.session_state.subsubcategory and st.session_state.subsubcategory != "" else None,
                    "description": description,
                    "amount_before_vat": amount_before_vat,
                    "vat_amount": st.session_state.vat_amount,
                    "total_amount": st.session_state.total_amount,
                    "entered_by": entered_by
                }
                st.session_state.session_expenses.append(expense_record)
                st.session_state.current_user = entered_by
                
                # Reset calculations without touching widget state
                st.session_state.vat_amount = 0.0
                st.session_state.total_amount = 0.0
                st.rerun()

def employee_view_page():
    st.header("👨‍💼 Employee Expense View")
    
    if 'current_user' not in st.session_state or not st.session_state.current_user:
        st.session_state.current_user = st.text_input("Enter your name to view your expenses")
        return
    
    st.subheader(f"Expenses entered in this session by {st.session_state.current_user}")
    
    if not st.session_state.session_expenses:
        st.info("No expenses recorded in this session")
    else:
        df = pd.DataFrame(st.session_state.session_expenses)
        
        # Add delete functionality
        df['Delete'] = False
        edited_df = st.data_editor(
            df,
            column_config={
                "Delete": st.column_config.CheckboxColumn(
                    "Delete?",
                    help="Check to delete this expense",
                    default=False
                )
            },
            disabled=["date", "category", "subcategory", "description", 
                    "amount_before_vat", "vat_amount", "total_amount", "entered_by"],
            hide_index=True
        )
        
        if edited_df['Delete'].any():
            indices_to_delete = edited_df[edited_df['Delete']].index.tolist()
            if st.button("Confirm Deletion"):
                st.session_state.session_expenses = [
                    exp for i, exp in enumerate(st.session_state.session_expenses)
                    if i not in indices_to_delete
                ]
                st.success("Selected expenses deleted!")
                st.rerun()
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            # CSV Download
            csv = df.drop(columns=['Delete']).to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Session Expenses (CSV)",
                csv,
                f"expenses_{st.session_state.current_user}_{datetime.now().date()}.csv",
                "text/csv"
            )
        with col2:
            # PDF Download
            pdf_bytes = generate_pdf_report(
                df.drop(columns=['Delete']),
                f"Expenses for {st.session_state.current_user}"
            )
            st.download_button(
                "Download Session Expenses (PDF)",
                data=pdf_bytes,
                file_name=f"expenses_{st.session_state.current_user}_{datetime.now().date()}.pdf",
                mime="application/pdf"
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
                    conn = sqlite3.connect('expense_tracker.db')
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
        # Display summary statistics
        st.subheader("Summary Statistics")
        total_expenses = filtered_expenses['total_amount'].sum()
        avg_expense = filtered_expenses['total_amount'].mean()
        num_expenses = len(filtered_expenses)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Expenses", f"SAR {total_expenses:,.2f}")
        col2.metric("Average Expense", f"SAR {avg_expense:,.2f}")
        col3.metric("Number of Expenses", num_expenses)
        
        # Display all expenses
        st.subheader("All Expense Records")
        st.dataframe(filtered_expenses, use_container_width=True)
        
        # PDF Download button for all expenses
        pdf_bytes = generate_pdf_report(filtered_expenses, f"Expense Report {start_date} to {end_date}")
        st.download_button(
            "Download All Expenses (PDF)",
            data=pdf_bytes,
            file_name=f"expenses_{start_date}_to_{end_date}.pdf",
            mime="application/pdf"
        )
        
        # Category breakdown
        st.subheader("Expense Analysis by Category")
        category_summary = get_category_summary(start_date, end_date)
        
        if not category_summary.empty:
            # Display as bar chart
            filtered_summary = category_summary[category_summary['category'] != 'TOTAL']
            st.bar_chart(
                filtered_summary.set_index('category')['total_amount'],
                use_container_width=True
            )
            
            # Display as table with grand total
            st.dataframe(category_summary, use_container_width=True)
            
            # PDF Download button for category summary
            pdf_bytes = generate_category_pdf_report(
                category_summary,
                f"Category Summary {start_date} to {end_date}"
            )
            st.download_button(
                "Download Category Summary (PDF)",
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
    
    if st.sidebar.radio("Login As", ["Employee", "Manager"]) == "Employee":
        page = st.sidebar.radio("Go to", ["Record Expense", "My Expenses"])
        
        if page == "Record Expense":
            record_expense_page()
        else:
            employee_view_page()
    else:
        manager_view_page()

if __name__ == "__main__":
    main()