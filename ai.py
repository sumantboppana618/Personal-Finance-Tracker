import os
import requests


def analyze_spending(transactions):
    api_key = os.environ.get("GEMINI_KEY")
    if not api_key:
        return {"summary": "AI unavailable: no API key configured."}

    expenses = [t for t in transactions if t.get("type") == "expense"]
    incomes = [t for t in transactions if t.get("type") == "income"]

    total_income = sum(float(t["amount"]) for t in incomes)
    total_expense = sum(float(t["amount"]) for t in expenses)

    category_totals = {}
    for t in expenses:
        cat = t.get("category", "other")
        category_totals[cat] = category_totals.get(cat, 0) + float(t["amount"])

    prompt = (
        "You are a personal finance advisor. Analyze this spending data "
        "and give brief, helpful advice.\n\n"
        f"Total Income: QAR {total_income}\n"
        f"Total Expenses: QAR {total_expense}\n"
        f"Balance: QAR {total_income - total_expense}\n\n"
        "Expense breakdown by category:\n"
        + "\n".join(f"- {cat}: QAR {amt}" for cat, amt in category_totals.items())
        + "\n\nGive 3-4 short bullet points: spending patterns, "
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
            }
        )
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"summary": text}
    except Exception as e:
        return {"summary": f"AI analysis failed: {str(e)}"}
