import os
import google.generativeai as genai


def analyze_spending(transactions):
    api_key = os.environ.get("GEMINI_KEY")
    if not api_key:
        return {"summary": "AI unavailable: no API key configured."}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    expenses = [t for t in transactions if t.get("type") == "expense"]
    incomes = [t for t in transactions if t.get("type") == "income"]

    total_income = sum(float(t["amount"]) for t in incomes)
    total_expense = sum(float(t["amount"]) for t in expenses)

    category_totals = {}
    for t in expenses:
        cat = t.get("category", "other")
        category_totals[cat] = category_totals.get(cat, 0) + float(t["amount"])

    prompt = f"""You are a personal finance advisor. Analyze this user's spending data and give brief, helpful advice.

Total Income: QAR {total_income}
Total Expenses: QAR {total_expense}
Balance: QAR {total_income - total_expense}

Expense breakdown by category:
{chr(10).join(f"- {cat}: QAR {amt}" for cat, amt in category_totals.items())}

Give 3-4 short bullet points: spending patterns, areas to cut back, and one saving tip. Keep it concise."""

    try:
        response = model.generate_content(prompt)
        return {"summary": response.text}
    except Exception as e:
        return {"summary": f"AI analysis failed: {str(e)}"}