"""
Prompt templates for the LangGraph agent.
"""

# ─── Vision prompt: reads the uploaded invoice image ──────
INVOICE_VISION_PROMPT = """You are a billing assistant. Look at this invoice/receipt image carefully.

Extract the following information:
1. Invoice number or receipt number (if visible)
2. Client/customer name (who is being billed)
3. Total amount (with currency)
4. Due date (if visible, otherwise say "Not specified")
5. List of items/services with their individual amounts
6. Any other important details (payment terms, notes, etc.)

Return ONLY valid JSON with this structure (no markdown fences, no extra text):
{{
  "invoice_id": "...",
  "client_name": "...",
  "total_amount": "...",
  "due_date": "...",
  "line_items": [
    {{"description": "...", "amount": "..."}},
  ],
  "notes": "..."
}}
"""

# ─── Email drafting prompt ────────────────────────────────
EMAIL_DRAFT_PROMPT = """You are a professional billing assistant at {company_name}.

Based on the following invoice data, write a professional email to send to the customer along with the invoice attachment.

Invoice Data:
- Invoice ID: {invoice_id}
- Client Name: {client_name}
- Total Amount: {total_amount}
- Due Date: {due_date}
- Items: {line_items}
- Notes: {notes}

Write a clear, professional email with:
1. A concise subject line
2. A professional greeting
3. A brief description of what the invoice is for
4. A summary table of items and amounts (in plain text, formatted nicely)
5. Payment instructions or deadline reminder
6. A professional closing

Return ONLY valid JSON (no markdown fences):
{{
  "subject": "...",
  "body": "..."
}}
"""
