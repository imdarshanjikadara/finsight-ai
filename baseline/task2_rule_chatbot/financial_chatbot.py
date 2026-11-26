"""
GFC Financial Chatbot - rule-based prototype
BCG GenAI Consulting Team | Task 2

Answers a small set of predefined financial questions about Microsoft, Tesla and
Apple (fiscal years 2023-2025) using the data extracted from their 10-K filings
in Task 1 (financial_data.csv).

How it works
  1. The CSV is loaded once into a nested dictionary: data[company][year][metric].
  2. Each user message is normalised (lower case, punctuation removed).
  3. Rule-based if/elif logic identifies WHAT is being asked (the query type),
     and simple keyword rules pick out WHICH company and year.
  4. The matching figure is fetched from the data and returned as a plain-English
     answer, followed by suggested follow-up questions.
  5. The bot remembers the last company and year (state), so follow-ups like
     "What about its cash flow?" work without repeating the company.

Run it:   python financial_chatbot.py
"""

import os
import re
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Data loading
# ---------------------------------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financial_data.csv")

COMPANY_ALIASES = {
    "microsoft": "Microsoft", "msft": "Microsoft",
    "tesla": "Tesla", "tsla": "Tesla",
    "apple": "Apple", "aapl": "Apple",
}

FISCAL_YEAR_END = {
    "Microsoft": "June 30",
    "Apple": "late September",
    "Tesla": "December 31",
}

PREDEFINED_QUERIES = [
    "What is the total revenue?",
    "How has net income changed over the last year?",
    "What is the net profit margin?",
    "What is the operating cash flow?",
    "How healthy is the balance sheet?",
]


def load_data(path=DATA_FILE):
    """Load the Task 1 CSV into {company: {year: {metric: value}}} (USD millions)."""
    df = pd.read_csv(path)
    data = {}
    for _, row in df.iterrows():
        data.setdefault(row["Company"], {})[int(row["Year"])] = {
            "revenue": float(row["Total Revenue"]),
            "net_income": float(row["Net Income"]),
            "assets": float(row["Total Assets"]),
            "liabilities": float(row["Total Liabilities"]),
            "ocf": float(row["Cash Flow from Operating Activities"]),
        }
    return data


# ---------------------------------------------------------------------------
# 2. Formatting helpers
# ---------------------------------------------------------------------------
def money(millions):
    """Format a USD-millions figure as '$101.8 billion'."""
    return f"${millions / 1000:,.1f} billion"


def pct_change(new, old):
    return (new - old) / abs(old) * 100


def text_bar(value, max_value, width=25):
    """A simple text bar so trends can be 'seen' in a command-line chat."""
    return "#" * max(1, round(value / max_value * width))


# ---------------------------------------------------------------------------
# 3. The chatbot
# ---------------------------------------------------------------------------
class FinancialChatbot:
    def __init__(self, data):
        self.data = data
        self.years = sorted({y for c in data.values() for y in c})
        self.latest_year = self.years[-1]
        # --- state management: remembered context ---
        self.company = None
        self.year = None
        self.unanswered = []  # questions the rules could not handle (useful for the NLP/ML team)

    # ---- parsing helpers ---------------------------------------------------
    @staticmethod
    def normalise(text):
        return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()

    def find_company(self, words):
        for w in words:
            if w in COMPANY_ALIASES:
                return COMPANY_ALIASES[w]
        return None

    @staticmethod
    def find_year(words):
        for w in words:
            if re.fullmatch(r"(19|20)\d\d", w):
                return int(w)
            if re.fullmatch(r"fy\d\d", w):          # e.g. "FY24"
                return 2000 + int(w[2:])
        return None

    # ---- main entry point --------------------------------------------------
    def respond(self, user_query):
        words = self.normalise(user_query)
        text = " ".join(words)

        if not words:
            return "Please type a question. Type 'help' to see what I can answer."

        # ---- commands ----
        if text in ("help", "menu", "options", "what can you do", "what can i ask"):
            return self.help_text()
        if text in ("exit", "quit", "bye", "goodbye"):
            return "Goodbye! Thanks for using the GFC Financial Chatbot."
        if text in ("reset", "clear", "start over"):
            self.company, self.year = None, None
            return "Context cleared. Which company would you like to look at: Microsoft, Tesla or Apple?"
        if text in ("hi", "hello", "hey"):
            return "Hello! Ask me about Microsoft, Tesla or Apple. Type 'help' for example questions."

        # ---- pick out company and year, update state ----
        company = self.find_company(words)
        year = self.find_year(words)
        if company:
            self.company = company
        if year:
            if year not in self.years:
                return (f"Sorry, I only have data for fiscal years "
                        f"{self.years[0]}-{self.years[-1]}, not {year}.")
            self.year = year

        # ---- rule-based query matching (if / elif) ----
        if any(k in words for k in ("buy", "sell", "invest", "investing", "shares", "stock", "recommend")):
            target = f" {self.company}'s" if self.company else ""
            return ("I can't give investment advice. I only report what the companies' 10-K filings show. "
                    f"To help you form your own view, try asking about{target} revenue, net income change, "
                    "profit margin, cash flow or balance sheet, or type 'compare all companies'.")
        elif "compare" in words or "all companies" in text:
            query_type = "compare"
        elif ("net income" in text or "profit" in words or "earnings" in words) and any(
                k in words for k in ("change", "changed", "grow", "grew", "growth",
                                     "increase", "increased", "decrease", "decreased", "trend")):
            query_type = "net_income_change"
        elif "margin" in words:
            query_type = "margin"
        elif "cash" in words:
            query_type = "cash_flow"
        elif any(k in words for k in ("revenue", "sales")):
            query_type = "revenue"
        elif "net income" in text or "profit" in words or "earnings" in words:
            query_type = "net_income_change"
        elif any(k in words for k in ("balance", "assets", "liabilities", "debt", "health", "healthy", "leverage")):
            query_type = "balance_sheet"
        elif company or year:
            # User only named a company/year, e.g. "Tell me about Apple"
            return self.overview()
        else:
            self.unanswered.append(user_query)
            return ("Sorry, I didn't understand that. I can answer these questions "
                    "(add a company name and, optionally, a year):\n" + self.query_list() +
                    "\nType 'help' for more examples.")

        if query_type == "compare":
            return self.compare()

        if self.company is None:
            return ("Which company do you mean: Microsoft, Tesla or Apple? "
                    "For example: 'What is the total revenue of Apple?'")

        handler = {
            "revenue": self.answer_revenue,
            "net_income_change": self.answer_net_income_change,
            "margin": self.answer_margin,
            "cash_flow": self.answer_cash_flow,
            "balance_sheet": self.answer_balance_sheet,
        }[query_type]
        return handler()

    # ---- context helpers ---------------------------------------------------
    def current(self):
        year = self.year or self.latest_year
        return self.company, year, self.data[self.company][year]

    def prior(self, company, year):
        return self.data[company].get(year - 1)

    def fy_label(self, company, year):
        return f"FY{year} (fiscal year ended {FISCAL_YEAR_END[company]}, {year})"

    @staticmethod
    def suggest(*questions):
        return "\n\nYou could also ask: " + " | ".join(f'"{q}"' for q in questions)

    # ---- the five predefined answers --------------------------------------
    def answer_revenue(self):
        c, y, d = self.current()
        msg = f"{c}'s total revenue in {self.fy_label(c, y)} was {money(d['revenue'])}."
        p = self.prior(c, y)
        if p:
            g = pct_change(d["revenue"], p["revenue"])
            msg += f" That is {'up' if g >= 0 else 'down'} {abs(g):.1f}% from {money(p['revenue'])} the year before."
        return msg + self.suggest("How has net income changed?", "What is the net profit margin?")

    def answer_net_income_change(self):
        c, y, d = self.current()
        p = self.prior(c, y)
        if not p:
            msg = (f"{c}'s net income in {self.fy_label(c, y)} was {money(d['net_income'])}. "
                   f"I don't have FY{y - 1} data to compare it with, so I can't show the change.")
        else:
            diff = d["net_income"] - p["net_income"]
            g = pct_change(d["net_income"], p["net_income"])
            direction = "increased" if diff >= 0 else "decreased"
            msg = (f"{c}'s net income {direction} by {money(abs(diff))} ({abs(g):.1f}%) over the last year, "
                   f"from {money(p['net_income'])} in FY{y - 1} to {money(d['net_income'])} in FY{y}.")
        # text chart of the full trend
        series = {yr: self.data[c][yr]["net_income"] for yr in self.years}
        top = max(series.values())
        msg += f"\n\n{c} net income trend:\n" + "\n".join(
            f"  FY{yr} {text_bar(v, top):<26} {money(v)}" for yr, v in series.items())
        return msg + self.suggest("What is the net profit margin?", "Compare all companies")

    def answer_margin(self):
        c, y, d = self.current()
        m = d["net_income"] / d["revenue"] * 100
        msg = (f"{c}'s net profit margin in FY{y} was {m:.1f}%. In plain terms, {c} kept about "
               f"${m / 100:.2f} of profit from every $1 of sales.")
        p = self.prior(c, y)
        if p:
            pm = p["net_income"] / p["revenue"] * 100
            trend = "improved" if m > pm else "declined" if m < pm else "was unchanged"
            msg += f" The margin {trend} from {pm:.1f}% in FY{y - 1}."
        return msg + self.suggest("What is the total revenue?", "What is the operating cash flow?")

    def answer_cash_flow(self):
        c, y, d = self.current()
        conv = d["ocf"] / d["net_income"]
        msg = (f"{c} generated {money(d['ocf'])} of cash from operating activities in FY{y}. "
               f"This is the cash the business produced from its day-to-day operations. "
               f"That is {conv:.2f}x its net income")
        msg += (", so its profits are well backed by real cash." if conv >= 1
                else ", so less cash came in than reported profit, which is worth watching.")
        p = self.prior(c, y)
        if p:
            g = pct_change(d["ocf"], p["ocf"])
            msg += f" Operating cash flow was {'up' if g >= 0 else 'down'} {abs(g):.1f}% from the year before."
        return msg + self.suggest("How healthy is the balance sheet?", "How has net income changed?")

    def answer_balance_sheet(self):
        c, y, d = self.current()
        ratio = d["liabilities"] / d["assets"] * 100
        equity = d["assets"] - d["liabilities"]
        if ratio < 50:
            view = "a conservative balance sheet: most of its assets are funded by shareholders' equity rather than obligations"
        elif ratio < 75:
            view = "a moderately leveraged balance sheet"
        else:
            view = ("a highly leveraged balance sheet. For a company with strong cash flow this can be a deliberate choice "
                    "(for example, returning cash to shareholders through buybacks) rather than a sign of distress")
        msg = (f"At the end of FY{y}, {c} had total assets of {money(d['assets'])} and total liabilities of "
               f"{money(d['liabilities'])}. Liabilities were {ratio:.1f}% of assets, leaving {money(equity)} "
               f"of equity. That indicates {view}.")
        return msg + self.suggest("What is the operating cash flow?", "Compare all companies")

    # ---- extras -------------------------------------------------------------
    def overview(self):
        if self.company is None:
            return "Which company would you like to look at: Microsoft, Tesla or Apple?"
        c, y, d = self.current()
        return (f"Here's a quick snapshot of {c} for {self.fy_label(c, y)}:\n"
                f"  Revenue:              {money(d['revenue'])}\n"
                f"  Net income:           {money(d['net_income'])}\n"
                f"  Total assets:         {money(d['assets'])}\n"
                f"  Total liabilities:    {money(d['liabilities'])}\n"
                f"  Operating cash flow:  {money(d['ocf'])}"
                + self.suggest("How has net income changed?", "What is the net profit margin?"))

    def compare(self):
        y = self.year or self.latest_year
        rows = []
        for c in sorted(self.data):
            d = self.data[c][y]
            rows.append((c, d["revenue"], d["net_income"], d["net_income"] / d["revenue"] * 100))
        rows.sort(key=lambda r: r[1], reverse=True)
        top = rows[0][1]
        lines = [f"FY{y} comparison (by revenue; fiscal years end on different dates):"]
        for c, rev, ni, m in rows:
            lines.append(f"  {c:<10} {text_bar(rev, top):<26} revenue {money(rev)}, "
                         f"net income {money(ni)}, margin {m:.1f}%")
        best = max(rows, key=lambda r: r[3])[0]
        lines.append(f"\n{rows[0][0]} has the most revenue; {best} has the highest profit margin.")
        return "\n".join(lines) + self.suggest("How healthy is Apple's balance sheet?", "How has Tesla's net income changed?")

    @staticmethod
    def query_list():
        return "\n".join(f"  {i}. {q}" for i, q in enumerate(PREDEFINED_QUERIES, 1))

    def help_text(self):
        return ("I answer questions about Microsoft, Tesla and Apple for fiscal years "
                f"{self.years[0]}-{self.years[-1]} (data from their 10-K filings).\n\n"
                "Predefined questions:\n" + self.query_list() +
                "\n\nExamples:\n"
                "  What is the total revenue of Microsoft?\n"
                "  How has Tesla's net income changed over the last year?\n"
                "  What is Apple's net profit margin in 2024?\n"
                "  Compare all companies\n\n"
                "Tips: name a company once and I'll remember it for follow-up questions. "
                f"With no year given, I use the latest year (FY{self.latest_year}).\n"
                "Commands: help, reset, exit")


# ---------------------------------------------------------------------------
# 4. Function interface, matching the task template
# ---------------------------------------------------------------------------
_bot = None


def simple_chatbot(user_query):
    """Return the chatbot's response to a single query (keeps context between calls)."""
    global _bot
    if _bot is None:
        _bot = FinancialChatbot(load_data())
    return _bot.respond(user_query)


# ---------------------------------------------------------------------------
# 5. Command-line chat loop
# ---------------------------------------------------------------------------
def main():
    bot = FinancialChatbot(load_data())
    print("=" * 70)
    print(" GFC Financial Chatbot (prototype) | Microsoft, Tesla, Apple | FY2023-FY2025")
    print("=" * 70)
    print(bot.help_text())
    print("-" * 70)
    while True:
        try:
            user_query = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break
        reply = bot.respond(user_query)
        print(f"\nBot: {reply}")
        if user_query.strip().lower() in ("exit", "quit", "bye", "goodbye"):
            break


if __name__ == "__main__":
    main()
