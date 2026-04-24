# ai_engine.py

import datetime

def analyze_finance(incomes, expenses):
    total_income = sum(i['amount'] for i in incomes)
    total_expense = sum(e['amount'] for e in expenses)
    balance = total_income - total_expense

    # Daily average expense
    days = max(1, (datetime.datetime.now() - datetime.timedelta(days=30)).day)
    daily_expense_avg = total_expense / 30

    # Prediction: days before money ends
    if daily_expense_avg > 0:
        days_left = int(balance / daily_expense_avg)
    else:
        days_left = "Unknown"

    # Advice
    if total_expense > total_income:
        advice = "Uri gukoresha amafaranga menshi kurusha ayo winjiza. Gabanya expenses."
    elif balance < 50000:
        advice = "Amafaranga asigaye ni make. Gerageza kwizigama."
    else:
        advice = "Ukoresha neza amafaranga yawe. Komereza aho."

    summary = f"""
    Total Income: {total_income} Frw
    Total Expenses: {total_expense} Frw
    Balance: {balance} Frw
    Estimated days before money ends: {days_left}
    """

    return summary, advice
