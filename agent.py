"""
LangGraph agent — two-node pipeline:
  1. extract_invoice  → Uses GPT-4o vision to read the uploaded invoice image
  2. draft_email      → Generates a professional email from the extracted data
"""

import json
import base64
from typing import Any, Dict, TypedDict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import streamlit as st
import config
from prompts import INVOICE_VISION_PROMPT, EMAIL_DRAFT_PROMPT


# ─── Graph State ──────────────────────────────────────────
class GraphState(TypedDict, total=False):
    image_data: List[str]         # list of base64-encoded images
    extracted_data: dict
    email_subject: str
    email_body: str
    error: str


# ─── LLM ─────────────────────────────────────────────────
def _get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=config.TEMPERATURE
    )


def _strip_json(text: str) -> str:
    """Remove markdown code fences if the LLM wraps its JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()

# ─── NODE 1: Extract invoice data (Groq-compatible) ─────────────
def extract_invoice(state: GraphState) -> Dict[str, Any]:
    llm = _get_llm()
    images = state.get("image_data", [])

    if not images:
        return {"error": "No images provided."}

    try:
        import base64

        # Convert base64 → bytes → OCR text
        img_bytes = base64.b64decode(images[0])
        from file_utils import image_to_text

        extracted_text = image_to_text(img_bytes)

        if not extracted_text.strip():
            return {"error": "OCR failed to extract text from image."}

        prompt = INVOICE_VISION_PROMPT + "\n\nInvoice text:\n" + extracted_text

        response = llm.invoke(prompt)

        data = json.loads(_strip_json(response.content))
        return {"extracted_data": data}

    except Exception as e:
        return {"error": f"Failed to read invoice: {e}"}

# ─── NODE 2: Draft the email ─────────────────────────────
def draft_email(state: GraphState) -> Dict[str, Any]:
    
    """Generate a professional email from extracted invoice data."""
    if state.get("error"):
        return {}

    data = state["extracted_data"]
    llm = _get_llm()

    # Format line items for the prompt
    items_str = ""
    for item in data.get("line_items", []):
        if isinstance(item, dict):
            items_str += f"  - {item.get('description', '?')}: {item.get('amount', '?')}\n"
        else:
            items_str += f"  - {item}\n"

    # Resolve sender details: config (sidebar) takes priority, then OCR-extracted, then fallback
    sender_name = config.SENDER_NAME or data.get("sender_company", "") or "Billing Department"
    sender_phone = config.SENDER_PHONE or data.get("sender_phone", "") or ""
    sender_email = config.SENDER_EMAIL or config.SMTP_EMAIL or data.get("sender_email", "") or ""
    company_name = config.COMPANY_NAME or data.get("sender_company", "") or "Our Company"

    prompt = EMAIL_DRAFT_PROMPT.format(
        company_name=company_name,
        invoice_id=data.get("invoice_id", "N/A"),
        client_name=data.get("client_name", "Customer"),
        total_amount=data.get("total_amount", "N/A"),
        due_date=data.get("due_date", "N/A"),
        line_items=items_str.strip(),
        notes=data.get("notes", ""),
        sender_name=sender_name,
        sender_phone=sender_phone if sender_phone else "N/A",
        sender_email=sender_email if sender_email else "N/A",
    )

    try:
        response = llm.invoke(prompt)
        email = json.loads(_strip_json(response.content))
        return {
            "email_subject": email.get("subject", ""),
            "email_body": email.get("body", ""),
        }
    except Exception as e:
        return {"error": f"Failed to draft email: {e}"}


# ─── Build Graph ─────────────────────────────────────────
def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("extract_invoice", extract_invoice)
    graph.add_node("draft_email", draft_email)
    graph.set_entry_point("extract_invoice")
    graph.add_edge("extract_invoice", "draft_email")
    graph.add_edge("draft_email", END)
    return graph.compile()


def run_agent(image_data: List[str]) -> Dict[str, Any]:
    """Run the full pipeline. `image_data` is a list of base64-encoded images."""
    app = build_graph()
    return app.invoke({"image_data": image_data})
