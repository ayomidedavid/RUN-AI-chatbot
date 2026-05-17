import os
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    print(f"Extracting text from {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
        full_text = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 1. Try direct text extraction first (fastest and most accurate for digital PDFs)
            text = page.get_text("text")
            
            # 2. Fallback to OCR if direct extraction yields very little text (likely a scanned image)
            if len(text.strip()) < 50:
                print(f"  Page {page_num+1}: Direct extraction failed/low yield, falling back to OCR...")
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                
                local_tessdata = os.path.abspath("tessdata")
                custom_config = r'--tessdata-dir {}'.format(local_tessdata)
                text = pytesseract.image_to_string(image, config=custom_config)
            
            full_text.append(text)
            print(f"Processed page {page_num + 1}/{len(doc)}")
        
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
        return ""

if __name__ == "__main__":
    # If running from root, data_dir is 'data'
    data_dir = "data"
    output_file = "backend/extracted_data.txt"
    
    # Process both datasets and handbooks
    pdf_files = [
        "First dataset.pdf", 
        "Second dataset.pdf", 
        "Third Dataset.pdf",
        "forth dataset.pdf",
        "student hand book/Computer Science BMAS handbook.pdf",
        "student hand book/Cyber Security handbook.pdf",
        "student hand book/information technology handbook.pdf"
    ]
    
    with open(output_file, "w", encoding="utf-8") as f:
        for pdf_name in pdf_files:
            pdf_path = os.path.join(data_dir, pdf_name)
            if os.path.exists(pdf_path):
                print(f"--- Processing {pdf_name} ---")
                text = extract_text_from_pdf(pdf_path)
                f.write(f"--- START OF {pdf_name} ---\n")
                f.write(text)
                f.write(f"\n--- END OF {pdf_name} ---\n\n")
            else:
                print(f"Could not find {pdf_path}")
    print(f"Extraction complete! Saved to {output_file}")
