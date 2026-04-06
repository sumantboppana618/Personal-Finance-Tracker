import os


def analyze_spending(transactions):
    expenses = [t for t in transactions if t.get("type") == "expense"]
    incomes = [t for t in transactions if t.get("type") == "income"]

    total_income = sum(float(t["amount"]) for t in incomes)
    total_expense = sum(float(t["amount"]) for t in expenses)

    category_totals = {}
    for t in expenses:
        cat = t.get("category", "other")
        category_totals[cat] = category_totals.get(cat, 0) + float(t["amount"])

    expense_breakdown = "\n".join(
        f"- {cat}: QAR {amt}" for cat, amt in category_totals.items()
    )

    def local_insight():
        if not expenses:
            return "No expenses yet. Add expenses to see spending insights."

        top_cat, top_amt = (
            max(category_totals.items(), key=lambda x: x[1])
            if category_totals
            else ("uncategorized", 0)
        )
        savings_tip = (
            "Try trimming QAR "
            f"{max(50, round(top_amt * 0.05, 2))} "
            f"from {top_cat} next week."
        )
        return (
            f"Expense focus: {top_cat} at QAR {top_amt}. "
            f"Total expense QAR {total_expense}, income QAR {total_income}, "
            f"balance QAR {total_income - total_expense}. {savings_tip}"
        )

    api_key = os.environ.get("GEMINI_KEY")
    if not api_key:
        return {"summary": local_insight()}

    try:
        import requests
    except ModuleNotFoundError:
        return {"summary": local_insight()}

    prompt = (
        "You are a personal finance advisor. Analyze this spending data "
        "and give brief, helpful advice.\n\n"
        f"Total Income: QAR {total_income}\n"
        f"Total Expenses: QAR {total_expense}\n"
        f"Balance: QAR {total_income - total_expense}\n\n"
        "Expense breakdown by category:\n"
        f"{expense_breakdown}\n\n"
        "Give 3-4 short bullet points: spending patterns, "
        "areas to cut back, and one saving tip. Keep it concise."
    )

    url = (
        "https://aiplatform.googleapis.com/v1/publishers/google/"
        "models/gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
            },
            timeout=15,
        )
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"summary": text}
    except Exception:
        return {"summary": local_insight()}
