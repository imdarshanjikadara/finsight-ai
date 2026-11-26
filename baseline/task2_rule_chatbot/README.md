# GFC Financial Chatbot: Rule-Based Prototype

**BCG GenAI Consulting Team · Client: Global Finance Corp. (GFC) · Task 2**

A command-line chatbot that answers predefined financial questions about **Microsoft, Tesla and Apple** for **fiscal years 2023–2025**. It uses the data extracted from their 10-K filings in Task 1.

## Files

| File | Purpose |
|---|---|
| `financial_chatbot.py` | The chatbot: data loading, rule-based logic, state management, error handling and the chat loop |
| `financial_data.csv` | The Task 1 dataset (USD millions, as reported in each year's 10-K) |
| `test_chatbot.py` | Automated tests plus a sample conversation |
| `test_results.txt` | Output of the tests (17/17 passed) and the full conversation transcript |
| `README.md` | This documentation |

## How to run

Requires Python 3 and pandas (`pip install pandas`).

```
python financial_chatbot.py     # start chatting; type 'exit' to quit
python test_chatbot.py          # run the tests and regenerate test_results.txt
```

The task template's function interface is also available:

```python
from financial_chatbot import simple_chatbot
simple_chatbot("What is the total revenue of Apple?")
```

## How it works

1. **Data structuring:** On start-up, `financial_data.csv` is loaded into a nested dictionary, `data[company][year][metric]`, so any figure can be fetched directly.
2. **Input cleaning:** Each message is converted to lower case and stripped of punctuation, so "WHAT IS THE TOTAL REVENUE OF TSLA???" is understood.
3. **Rule-based matching:** An `if / elif` chain of keyword rules decides which question type is being asked. For example, "revenue" or "sales" means a revenue question, and "net income" plus "change" or "grow" means a net income change question. Separate rules detect the company (including tickers such as MSFT, TSLA and AAPL) and the year (for example 2024 or FY24).
4. **Retrieval and response:** The matching figures are fetched from the data. The bot calculates year-over-year changes and ratios, then returns a plain-English answer that names the fiscal year.
5. **State management:** The bot remembers the last company and year. After "Tell me about Apple", the template question "What is the total revenue?" is answered for Apple, and "What about its cash flow?" works as a follow-up. With no year given, it uses the latest year, FY2025.
6. **Engagement:** Each answer ends with suggested follow-up questions. Net income answers include a text bar chart of the three-year trend, and comparisons include text bars across companies.

## Predefined queries

Add a company name to any question, and optionally a year.

| # | Query | What the bot answers |
|---|---|---|
| 1 | What is the total revenue? | Revenue for the year and the % change from the prior year |
| 2 | How has net income changed over the last year? | The $ and % change in net income, plus a three-year text chart |
| 3 | What is the net profit margin? | Net income ÷ revenue, explained as "cents of profit per $1 of sales", and its trend |
| 4 | What is the operating cash flow? | Cash from operations, its year-over-year change and how well it covers net income |
| 5 | How healthy is the balance sheet? | Assets, liabilities, the liabilities-to-assets ratio, equity and a plain-English verdict |

**Extras:** "Tell me about <company>" gives a snapshot, "Compare all companies" gives a side-by-side view, and the commands are `help`, `reset` and `exit`.

## Error handling

| Situation | Bot behaviour |
|---|---|
| The question isn't recognized | Says so, lists the predefined questions and points to `help`. The question is logged in `bot.unanswered`. |
| No company named yet | Asks which company: Microsoft, Tesla or Apple |
| A year outside FY2023–2025 | Says which years are available |
| A change is requested for FY2023 | Explains there is no FY2022 data to compare against |
| An investment-advice request ("Should I buy…") | Declines, because it only reports filing data, and suggests factual questions instead |
| Empty input | Asks for a question |

## Example

```
You: How has Tesla's net income changed over the last year?
Bot: Tesla's net income decreased by $3.3 billion (46.5%) over the last year,
     from $7.1 billion in FY2024 to $3.8 billion in FY2025.

     Tesla net income trend:
       FY2023 #########################  $15.0 billion
       FY2024 ############               $7.1 billion
       FY2025 ######                     $3.8 billion
```

## Limitations

- **Keyword rules, not true language understanding.** Questions phrased very differently, or with typos (for example "revnue" or "Micro soft"), won't match. Questions that combine two metrics only get one answer.
- **Small, fixed scope.** It covers only three companies, three fiscal years and five figures from annual 10-Ks, with no quarterly 10-Q data. The data is a static CSV, not a live feed.
- **Simple context memory.** It remembers only the last company and year, and pronouns such as "it" or "they" aren't resolved explicitly.
- **Fiscal years differ.** Microsoft's year ends in June, Apple's in September and Tesla's in December, so year-to-year comparisons across companies are approximate. The bot states this in its comparisons.
- **No qualitative context.** It reports figures and ratios, but not the reasons behind them (for example one-time items described in the 10-K text), and it doesn't give investment advice.
- **Command-line only.** There's no web or chat interface yet.

## Next steps (handover to the wider team)

- **NLP:** Replace the keyword rules with intent classification and entity extraction, so varied wording and typos are understood.
- **ML / GenAI:** Use the logged `unanswered` questions as training data. Add an LLM layer that is grounded in this dataset, so it can give explanations without inventing numbers.
- **Data integration:** Load the figures automatically from SEC EDGAR's XBRL data, so the bot can scale to more companies and to quarterly 10-Q filings.
- **UX:** Wrap `FinancialChatbot.respond()` in a web interface (for example Flask) and replace the text bars with real charts.
