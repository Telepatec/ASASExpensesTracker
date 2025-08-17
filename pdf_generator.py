from fpdf import FPDF
from datetime import datetime
import pandas as pd

def generate_pdf_report(df, title):
    """Generate a PDF report from a DataFrame"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align="C")
    pdf.ln(10)
    
    # Column widths
    col_widths = [25, 35, 35, 35, 20, 20, 20]
    
    # Table header
    headers = ["Date", "Category", "Subcategory", "Description", "Before VAT", "VAT", "Total"]
    pdf.set_font("Arial", 'B', 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, txt=header, border=1)
    pdf.ln()
    
    # Table rows
    pdf.set_font("Arial", size=8)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, txt=str(row['date'])[:10], border=1)
        pdf.cell(col_widths[1], 10, txt=str(row['category']), border=1)
        pdf.cell(col_widths[2], 10, txt=str(row['subcategory']) if pd.notna(row['subcategory']) else "", border=1)
        pdf.cell(col_widths[3], 10, txt=str(row['description']), border=1)
        pdf.cell(col_widths[4], 10, txt=f"{row['amount_before_vat']:.2f}", border=1)
        pdf.cell(col_widths[5], 10, txt=f"{row['vat_amount']:.2f}", border=1)
        pdf.cell(col_widths[6], 10, txt=f"{row['total_amount']:.2f}", border=1)
        pdf.ln()
    
    # Add total if it's not a summary report
    if 'total_amount' in df.columns and len(df) > 0:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(sum(col_widths[:-1]), 10, txt="TOTAL:", align='R')
        pdf.cell(col_widths[-1], 10, txt=f"{df['total_amount'].sum():.2f}", border=1)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_category_pdf_report(df, title):
    """Generate a PDF report for category summaries"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align="C")
    pdf.ln(10)
    
    # Column widths
    col_widths = [60, 60, 60]
    
    # Table header
    headers = ["Category", "Subcategory", "Total Amount"]
    pdf.set_font("Arial", 'B', 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, txt=header, border=1)
    pdf.ln()
    
    # Table rows
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, txt=str(row['category']), border=1)
        pdf.cell(col_widths[1], 10, txt=str(row['subcategory']) if pd.notna(row['subcategory']) else "", border=1)
        pdf.cell(col_widths[2], 10, txt=f"{row['total_amount']:.2f}", border=1)
        pdf.ln()
    
    # Add total if it's a summary report
    if 'total_amount' in df.columns and len(df) > 0:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(sum(col_widths[:-1]), 10, txt="TOTAL:", align='R')
        pdf.cell(col_widths[-1], 10, txt=f"{df['total_amount'].sum():.2f}", border=1)
    
    return pdf.output(dest='S').encode('latin-1')