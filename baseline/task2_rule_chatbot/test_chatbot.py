"""
Tests for the GFC Financial Chatbot prototype.

Part 1 runs automatic checks: each predefined query must return the figure that
matches financial_data.csv, and state, follow-ups and error handling must behave
as designed.
Part 2 replays a sample conversation and saves the full transcript to
test_results.txt as evidence for the submission.

Run it:   python test_chatbot.py
"""

import os
from financial_chatbot import FinancialChatbot, load_data

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(HERE, "test_results.txt")

# (description, list of queries sent in order, text the LAST reply must contain)
CHECKS = [
    ("Q1 revenue (latest year by default)",
     ["What is the total revenue of Microsoft?"], ["$281.7 billion", "up 14.9%"]),
    ("Q1 revenue for a specific year",
     ["What is Apple's total revenue in 2024?"], ["$391.0 billion", "up 2.0%"]),
    ("Q2 net income change",
     ["How has Tesla's net income changed over the last year?"], ["decreased", "46.5%", "$7.1 billion", "$3.8 billion"]),
    ("Q2 net income change, first year (no prior data)",
     ["How has Apple's net income changed in 2023?"], ["don't have FY2022 data"]),
    ("Q3 net profit margin",
     ["What is the net profit margin of Microsoft?"], ["36.1%", "improved"]),
    ("Q4 operating cash flow",
     ["What is Apple's operating cash flow?"], ["$111.5 billion", "down 5.7%"]),
    ("Q5 balance sheet health",
     ["How healthy is Tesla's balance sheet?"], ["39.9%", "conservative"]),
    ("Exact template query uses remembered company (state)",
     ["Tell me about Apple", "What is the total revenue?"], ["Apple's total revenue", "$416.2 billion"]),
    ("Follow-up without naming the company (state)",
     ["What is Microsoft's revenue?", "What about its cash flow?"], ["Microsoft generated $136.2 billion"]),
    ("Year remembered across follow-ups",
     ["Tesla revenue in 2024", "and the margin?"], ["FY2024", "7.3%"]),
    ("Comparison across companies",
     ["Compare all companies"], ["Apple has the most revenue", "Microsoft has the highest profit margin"]),
    ("No company given yet: bot asks which one",
     ["What is the total revenue?"], ["Which company do you mean"]),
    ("Year outside dataset is handled",
     ["What was Microsoft's revenue in 2019?"], ["only have data for fiscal years 2023-2025"]),
    ("Unrecognised query is handled gracefully",
     ["What's the weather like today?"], ["Sorry, I didn't understand", "What is the total revenue?"]),
    ("Investment-advice request is declined",
     ["Should I buy Tesla stock?"], ["can't give investment advice"]),
    ("Help command",
     ["help"], ["Predefined questions"]),
    ("Case and punctuation insensitive",
     ["WHAT IS THE TOTAL REVENUE OF TSLA???"], ["Tesla's total revenue", "$94.8 billion"]),
]

CONVERSATION = [
    "hello",
    "What is the total revenue?",
    "Tell me about Microsoft",
    "What is the total revenue?",
    "How has net income changed over the last year?",
    "What is the net profit margin?",
    "What is the operating cash flow?",
    "How healthy is the balance sheet?",
    "Now Tesla",
    "How has net income changed over the last year?",
    "What is Apple's net profit margin in 2024?",
    "Compare all companies",
    "What was revenue in 2021?",
    "Should I buy Tesla stock?",
    "help",
    "exit",
]


def run_checks(data):
    results = []
    for desc, queries, expected in CHECKS:
        bot = FinancialChatbot(data)  # fresh bot for each check
        reply = ""
        for q in queries:
            reply = bot.respond(q)
        missing = [e for e in expected if e not in reply]
        results.append((desc, queries, not missing, missing))
    return results


def main():
    data = load_data()
    results = run_checks(data)
    passed = sum(ok for _, _, ok, _ in results)

    out = ["GFC FINANCIAL CHATBOT - TEST RESULTS", "=" * 70, "",
           f"PART 1: AUTOMATIC CHECKS ({passed}/{len(results)} passed)", "-" * 70]
    for desc, queries, ok, missing in results:
        out.append(f"[{'PASS' if ok else 'FAIL'}] {desc}")
        out.append(f"        input: {' -> '.join(queries)}")
        if missing:
            out.append(f"        missing from reply: {missing}")

    out += ["", "PART 2: SAMPLE CONVERSATION TRANSCRIPT", "-" * 70]
    bot = FinancialChatbot(data)
    for q in CONVERSATION:
        out.append(f"\nYou: {q}")
        out.append(f"Bot: {bot.respond(q)}")
    out += ["", "-" * 70,
            f"Queries the rules could not answer (logged for the NLP/ML team): {bot.unanswered}"]

    report = "\n".join(out)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    print(f"\nSaved to {RESULTS_FILE}")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
