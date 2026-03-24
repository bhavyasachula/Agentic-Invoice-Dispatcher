"""
Configuration — loads .env and exposes settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# GroQOpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "openai/gpt-oss-120b"
TEMPERATURE: float = 0.7

# SMTP (for sending emails)

SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

# Company
COMPANY_NAME: str = ""
