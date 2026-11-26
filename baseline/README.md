# v0 baseline: BCG GenAI job simulation (Forage)

This folder is a frozen snapshot of the original work, kept as the starting point
the rest of FinSight AI is measured against. It is not edited or linted.

## Task 1: Financial data extraction and analysis (`task1_analysis/`)
- Key figures (revenue, net income, total assets, total liabilities, operating
  cash flow) for Microsoft, Tesla and Apple, FY2023 to FY2025, from their 10-K filings.
- Jupyter notebook with year-over-year growth, financial ratios and findings.

## Task 2: Rule-based financial chatbot (`task2_rule_chatbot/`)
- Command-line chatbot that answers 5 predefined questions using keyword rules.
- Run: `uv run python financial_chatbot.py` · Tests: `uv run python test_chatbot.py`

## Limitations that motivate the rest of the project
- Only 3 companies, 3 years and 5 metrics, entered as a static CSV.
- Keyword rules: no real language understanding, and no access to the filing text.
- No measured accuracy beyond hand-written checks.