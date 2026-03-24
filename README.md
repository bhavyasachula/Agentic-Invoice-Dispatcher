# 📨 Agentic Invoice Dispatcher

AI agent that reads invoices (PDF/images), extracts data using OCR, drafts professional emails, and sends them to customers.

## Stack

* **Streamlit** — UI
* **LangGraph** — Agent pipeline
* **Groq (LLM)** — Text reasoning & email generation
* **Tesseract OCR** — Invoice text extraction
* **SMTP** — Email delivery

## How it works

```
Upload Invoice (PDF/Image)
        │
        ▼
  ┌────────────┐
  │ Tesseract  │  ← Extracts text from invoice
  │   OCR      │
  └─────┬──────┘
        │
        ▼
  ┌────────────┐
  │   Groq     │  ← Converts text → structured data
  │    LLM     │  ← Extracts: ID, client, amount, items, due date
  └─────┬──────┘
        │
        ▼
  ┌────────────┐
  │  Draft     │  ← Generates subject + body
  │  Email     │
  └─────┬──────┘
        │
        ▼
  Human Review (edit subject/body)
        │
        ▼
  Send via SMTP (with invoice attached)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your keys
streamlit run app.py
```

## Environment Variables

```
GROQ_API_KEY=your_groq_api_key

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Tesseract Setup

Install Tesseract OCR from:
https://github.com/UB-Mannheim/tesseract/wiki

Default install path:

```
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Make sure this path is set in your code if not detected automatically.

## Files

| File              | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `app.py`          | Streamlit UI (upload → review → send)      |
| `agent.py`        | LangGraph pipeline (OCR → extract → draft) |
| `prompts.py`      | Prompt templates                           |
| `file_utils.py`   | OCR + file processing                      |
| `email_sender.py` | SMTP email dispatch                        |
| `config.py`       | Settings & env loading                     |
| `models.py`       | Data models                                |

## Gmail Setup

To send emails via Gmail:

1. Enable 2-Factor Authentication
2. Go to Google Account → Security → App Passwords
3. Generate an app password for "Mail"
4. Use that password in `SMTP_PASSWORD`

## Notes

* OCR accuracy depends on invoice quality
* Works best with clear, typed invoices
* Handwritten invoices may not perform well
