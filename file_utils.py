
import pytesseract

import os

# Only set path for LOCAL (Windows)
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import base64
import io
from typing import List

import fitz  # PyMuPDF
from PIL import Image

import os

import numpy as np
import pytesseract

def image_to_text(img_bytes: bytes) -> str:
    # Only set path for Windows (local)
    if os.name == "nt":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Convert bytes → PIL Image
    image = Image.open(io.BytesIO(img_bytes)).convert("L")  # grayscale

    # Simple threshold (similar to cv2)
    image = image.point(lambda x: 0 if x < 150 else 255, '1')

    # OCR
    text = pytesseract.image_to_string(image)

    return text

def file_to_images_b64(file_bytes: bytes, file_name: str) -> List[str]:
    """
    Convert an uploaded file to a list of base64-encoded PNG images.
    - PDF  → one image per page
    - Image → single image (resized if huge)
    """
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""

    if ext == "pdf":
        return _pdf_to_images(file_bytes)
    else:
        return [_image_to_b64(file_bytes)]


def _pdf_to_images(pdf_bytes: bytes) -> List[str]:
    """Render each PDF page as a PNG image."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        # Render at 2x for clarity
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        images.append(base64.b64encode(img_bytes).decode("utf-8"))
    doc.close()
    return images


def _image_to_b64(img_bytes: bytes) -> str:
    """Resize large images and return base64 PNG."""
    img = Image.open(io.BytesIO(img_bytes))
    # Cap at 2000px on the longest side
    max_dim = 2000
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
