from datetime import datetime, timedelta

def calculate_vat(amount_before_vat, vat_rate=0.15):
    """Calculate VAT and total amount based on before VAT amount"""
    vat_amount = round(amount_before_vat * vat_rate, 2)
    total_amount = round(amount_before_vat + vat_amount, 2)
    return vat_amount, total_amount

def get_period_dates(period):
    today = datetime.today().date()
    if period == "1st-10th":
        return today.replace(day=1), today.replace(day=10)
    elif period == "11th-20th":
        return today.replace(day=11), today.replace(day=20)
    elif period == "21st-end":
        start_date = today.replace(day=21)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        return start_date, end_date
    return None, None