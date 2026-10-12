"""Natural-language interface to the Country Club SQLite database."""
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE = Path(__file__).parent
DB_PATH = BASE / "countryclub.sqlite"
load_dotenv(BASE / ".env")

# Cheapest OpenAI chat model ($0.10 / 1M input tokens, $0.40 / 1M output tokens).
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
PRICE_IN, PRICE_OUT = 0.10 / 1_000_000, 0.40 / 1_000_000

SCHEMA = (BASE / "schema.sql").read_text(encoding="utf-8")

NOTES = (
    "\n-- Notes: SQLite dialect. Boolean columns (is_active, auto_renew) are stored as 1/0. "
    "Dates are ISO text (YYYY-MM-DD); timestamps are 'YYYY-MM-DD HH:MM:SS'. "
    "Today's date is 2026-10-12. Revenue means payments with payment_status = 'Completed'.\n"
)

SQL_ONLY = (" Give me a sqlite select statement that answers the question. "
            "Only respond with sqlite syntax. If there is an error do not explain it!")

# Cross-domain example from a different database (paper's "multi-domain" idea).
OTHER_DOMAIN = (
    "\n-- Example from a DIFFERENT database (a veterinary clinic):\n"
    "-- CREATE TABLE owner(owner_id INTEGER PRIMARY KEY, name TEXT);\n"
    "-- CREATE TABLE pet(pet_id INTEGER PRIMARY KEY, owner_id INTEGER REFERENCES owner, name TEXT, species TEXT);\n"
    "-- Q: Which owners have more than one pet?\n"
    "SELECT o.name, COUNT(*) AS pets FROM owner o JOIN pet p ON p.owner_id = o.owner_id "
    "GROUP BY o.owner_id HAVING COUNT(*) > 1;\n"
)
# Same-domain example using our own schema.
SAME_DOMAIN = (
    "\n-- Example for THIS database:\n"
    "-- Q: Which members have no email address on file?\n"
    "SELECT first_name, last_name FROM Member WHERE email IS NULL;\n"
)

STRATEGIES = {
    "zero_shot": SCHEMA + NOTES + SQL_ONLY,
    "single_domain_double_shot": SCHEMA + NOTES + SAME_DOMAIN + SQL_ONLY,
    "multi_domain_double_shot": SCHEMA + NOTES + OTHER_DOMAIN + SQL_ONLY,
}

_client = None


def client():
    global _client
    if _client is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY missing - put it in .env")
        _client = OpenAI()
    return _client


def chat(prompt):
    r = client().chat.completions.create(
        model=MODEL, temperature=0, messages=[{"role": "user", "content": prompt}])
    u = r.usage
    return r.choices[0].message.content or "", u.prompt_tokens, u.completion_tokens


def extract_sql(text):
    m = re.search(r"```(?:\w+)?\n?(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip().rstrip(";").strip()


def run_sql(sql):
    """Execute read-only; only a single SELECT/WITH statement is allowed."""
    if ";" in sql or not re.match(r"^\s*(select|with)\b", sql, re.I):
        raise ValueError("Only a single SELECT statement is allowed.")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchmany(200)
    finally:
        con.close()


def ask(question, strategy="zero_shot"):
    res = {"question": question, "strategy": strategy, "model": MODEL,
           "sql": None, "columns": [], "rows": [], "answer": None, "error": None}
    tin = tout = 0
    try:
        raw, a, b = chat(f"{STRATEGIES[strategy]} {question}")
        tin, tout = tin + a, tout + b
        res["sql"] = extract_sql(raw)
        res["columns"], rows = run_sql(res["sql"])
        res["rows"] = [list(r) for r in rows]
        prompt = (f'The user asked: "{question}"\nThe SQL query run was:\n{res["sql"]}\n'
                  f'Columns: {res["columns"]}\nResult rows (up to 200): {res["rows"]}\n'
                  "Answer the user's question in a concise, friendly natural-language reply "
                  "using only this data. If the result is empty, say no matching data was found. "
                  "No suggestions or extra chatter.")
        res["answer"], a, b = chat(prompt)
        tin, tout = tin + a, tout + b
    except Exception as e:  # surfaced to the UI
        res["error"] = f"{type(e).__name__}: {e}"
    res["tokens"] = {"input": tin, "output": tout}
    res["cost_usd"] = round(tin * PRICE_IN + tout * PRICE_OUT, 6)
    return res


def build_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    con.executescript((BASE / "data.sql").read_text(encoding="utf-8"))
    con.commit()
    con.close()
