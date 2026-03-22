import requests
import fitz  # PyMuPDF
import tempfile
import os
import io

def extract_text_from_pdf(url: str) -> str:
    """
    Downloads a PDF from a URL and extracts its text cleanly.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return f"Error downloading PDF from {url}: {e}"

    text_content = []
    
    try:
        # Open PDF from memory
        pdf_stream = io.BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extract text preserving physical layout where possible
            page_text = page.get_text("text") 
            if page_text.strip():
                text_content.append(page_text)
                
        doc.close()
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

    full_text = "\n".join(text_content)
    # Basic cleanup: remove excessive newlines
    clean_text = "\n".join([line for line in full_text.split("\n") if line.strip() != ""])
    
    return clean_text
