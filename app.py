"""
Streamlit app — Agentic Invoice Dispatcher

Flow:
  1. User uploads invoice (PDF / image) + enters customer email
  2. Agent extracts data & drafts email
  3. User reviews → can edit subject & body (human-in-the-loop)
  4. User clicks Send → email dispatched with invoice attached
"""

import json
import streamlit as st
import os

os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from agent import run_agent  # AFTER setting env ✅
import config
from file_utils import file_to_images_b64
from email_sender import send_email

# ─── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Invoice Dispatcher",
    page_icon="📨",
    layout="centered",
)

# ─── Minimal custom CSS ──────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container { max-width: 720px; }

    .step-label {
        display: inline-block;
        background: #2563eb;
        color: white;
        border-radius: 50%;
        width: 28px; height: 28px;
        text-align: center;
        line-height: 28px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar — settings ──────────────────────────────────
with st.sidebar:
    st.header("Settings")

    

    st.markdown("---")
    st.subheader("SMTP (Email)") 

    config.SMTP_EMAIL = st.text_input("Your Email", value=config.SMTP_EMAIL)
    config.SMTP_PASSWORD = st.text_input("App Password", type="password", value=config.SMTP_PASSWORD)
    config.SMTP_HOST = st.text_input("SMTP Host", value=config.SMTP_HOST)
    config.SMTP_PORT = int(st.text_input("SMTP Port", value=str(config.SMTP_PORT)))

    st.markdown("---")
    st.subheader("Sender Details")
    config.COMPANY_NAME = st.text_input("Company Name", value=config.COMPANY_NAME)
    config.SENDER_NAME = st.text_input("Your Name", value=config.SENDER_NAME)
    config.SENDER_PHONE = st.text_input("Phone Number", value=config.SENDER_PHONE)
    config.SENDER_EMAIL = st.text_input("Sender Email (for sign-off)", value=config.SENDER_EMAIL or config.SMTP_EMAIL)

# ─── Title ────────────────────────────────────────────────
st.title("📨 Invoice Dispatcher")
st.caption("Upload an invoice → AI drafts an email → Review & send.")
st.markdown("---")

# ─── Session state init ──────────────────────────────────
for key in ["agent_result", "subject", "body", "step", "file_bytes", "file_name"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "step" not in st.session_state or st.session_state["step"] is None:
    st.session_state["step"] = "upload"  # upload → review → done


# ═══════════════════════════════════════════════════════════
# STEP 1: Upload invoice + enter email
# ═══════════════════════════════════════════════════════════
if st.session_state["step"] == "upload":
    st.markdown('<span class="step-label">1</span> **Upload Invoice & Enter Details**', unsafe_allow_html=True)
    st.write("")

    uploaded = st.file_uploader(
        "Upload invoice (PDF, PNG, JPG, JPEG)",
        type=["pdf", "png", "jpg", "jpeg"],
    )

    customer_email = st.text_input("Customer email address")

    st.write("")
    process_btn = st.button("Process Invoice", type="primary")

    if process_btn:
        # Validations
        if not uploaded:
            st.error("Please upload an invoice file.")
        elif not customer_email or "@" not in customer_email:
            st.error("Please enter a valid customer email address.")
        else:
            file_bytes = uploaded.read()
            file_name = uploaded.name

            st.session_state["file_bytes"] = file_bytes
            st.session_state["file_name"] = file_name
            st.session_state["customer_email"] = customer_email

            with st.status("AI Agent is processing your invoice...", expanded=True) as status:
                st.write("Converting file to images...")
                images_b64 = file_to_images_b64(file_bytes, file_name)

                st.write(f"Extracted {len(images_b64)} page(s). Sending...")
                result = run_agent(images_b64)

                if result.get("error"):
                    status.update(label="Error", state="error")
                    st.error(result["error"])
                else:
                    status.update(label="Done!", state="complete")
                    st.session_state["agent_result"] = result
                    st.session_state["subject"] = result.get("email_subject", "")
                    st.session_state["body"] = result.get("email_body", "")
                    st.session_state["step"] = "review"
                    st.rerun()


# ═══════════════════════════════════════════════════════════
# STEP 2: Review & Edit (human-in-the-loop)
# ═══════════════════════════════════════════════════════════
elif st.session_state["step"] == "review":
    result = st.session_state["agent_result"]
    data = result.get("extracted_data", {})

    st.markdown('<span class="step-label">2</span> **Review & Edit Draft**', unsafe_allow_html=True)
    st.write("")

    # Show extracted data
    with st.expander("Extracted Invoice Data", expanded=False):
        st.json(data)

    st.markdown(f"**To:** {st.session_state.get('customer_email', '')}")
    st.markdown(f"**Attachment:** {st.session_state.get('file_name', '')}")
    st.write("")

    # Editable fields
    st.session_state["subject"] = st.text_input(
        "Subject",
        value=st.session_state["subject"],
    )

    st.session_state["body"] = st.text_area(
        "Email Body",
        value=st.session_state["body"],
        height=300,
    )

    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("✅ Send Email", type="primary", use_container_width=True):
            st.session_state["step"] = "sending"
            st.rerun()

    with col2:
        if st.button("🔄 Re-generate", use_container_width=True):
            # Re-run agent
            images_b64 = file_to_images_b64(
                st.session_state["file_bytes"],
                st.session_state["file_name"],
            )
            with st.spinner("Re-generating..."):
                result = run_agent(images_b64)
            if not result.get("error"):
                st.session_state["agent_result"] = result
                st.session_state["subject"] = result.get("email_subject", "")
                st.session_state["body"] = result.get("email_body", "")
            st.rerun()

    with col3:
        if st.button("❌ Cancel", use_container_width=True):
            for key in ["agent_result", "subject", "body", "file_bytes", "file_name", "customer_email"]:
                st.session_state[key] = None
            st.session_state["step"] = "upload"
            st.rerun()


# ═══════════════════════════════════════════════════════════
# STEP 3: Send
# ═══════════════════════════════════════════════════════════
elif st.session_state["step"] == "sending":
    st.markdown('<span class="step-label">3</span> **Sending Email...**', unsafe_allow_html=True)

    with st.spinner("Sending email..."):
        result_msg = send_email(
            to_email=st.session_state["customer_email"],
            subject=st.session_state["subject"],
            body=st.session_state["body"],
            attachment_bytes=st.session_state["file_bytes"],
            attachment_filename=st.session_state["file_name"],
        )

    if result_msg == "ok":
        st.session_state["step"] = "done"
        st.rerun()
    else:
        st.error(result_msg)
        st.session_state["step"] = "review"


# ═══════════════════════════════════════════════════════════
# STEP 4: Done
# ═══════════════════════════════════════════════════════════
elif st.session_state["step"] == "done":
    st.markdown('<span class="step-label">✓</span> **Email Sent Successfully!**', unsafe_allow_html=True)
    st.write("")
    st.success(
        f"Invoice **{st.session_state.get('file_name', '')}** has been emailed to "
        f"**{st.session_state.get('customer_email', '')}**."
    )

    st.write("")
    if st.button("Send Another Invoice", type="primary"):
        for key in ["agent_result", "subject", "body", "file_bytes", "file_name", "customer_email"]:
            st.session_state[key] = None
        st.session_state["step"] = "upload"
        st.rerun()
