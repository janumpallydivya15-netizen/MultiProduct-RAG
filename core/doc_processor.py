import os
import pymupdf  # PyMuPDF
import re
import hashlib
from typing import List, Dict, Any
from PIL import Image
import io
import config
from core.ocr_engine import OCREngine

class DocumentProcessor:
    def __init__(self, ocr_engine: OCREngine = None):
        self.ocr_engine = ocr_engine or OCREngine()

    def process_file(self, file_path: str, doc_id: str, product_id: str = "general", original_filename: str = None) -> Dict[str, Any]:
        """Main entry point to parse PDF, TXT, or MD file into structured chunks with metadata."""
        ext = os.path.splitext(file_path)[1].lower()
        filename = original_filename or os.path.basename(file_path)
        doc_type = ext.replace('.', '')

        if ext == ".pdf":
            pages_data = self._parse_pdf(file_path)
        elif ext in [".txt", ".md"]:
            pages_data = self._parse_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        total_pages = len(pages_data)
        chunks = self._chunk_pages(pages_data, doc_id=doc_id, filename=filename, product_id=product_id, doc_type=doc_type)

        return {
            "total_pages": total_pages,
            "chunks": chunks
        }

    def _clean_text(self, text: str) -> str:
        """Clean unnecessary whitespace while preserving paragraph structure."""
        if not text:
            return ""
        # Replace non-breaking spaces and control characters
        text = text.replace('\xa0', ' ').replace('\r\n', '\n').replace('\r', '\n')
        # Collapse multiple inline spaces and empty lines
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
        cleaned = '\n'.join(line for line in lines if line)
        return cleaned

    def _parse_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        pages_data = []
        doc = pymupdf.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = self._clean_text(text)

            # Fallback to OCR if page has insufficient native text (scanned PDF page)
            if len(cleaned_text) < 30:
                print(f"[DocProcessor] Low native text count on page {page_num+1} ({len(cleaned_text)} chars). Running EasyOCR fallback...")
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = self.ocr_engine.extract_text_from_pil(img)
                cleaned_ocr = self._clean_text(ocr_text)
                if cleaned_ocr:
                    cleaned_text = f"[OCR Extracted Content]\n{cleaned_ocr}"

            pages_data.append({
                "page_number": page_num + 1,
                "text": cleaned_text
            })

        doc.close()
        return pages_data

    def _parse_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        cleaned_content = self._clean_text(content)
        return [{
            "page_number": 1,
            "text": cleaned_content
        }]

    def _chunk_pages(self, pages_data: List[Dict[str, Any]], doc_id: str, filename: str, product_id: str, doc_type: str) -> List[Dict[str, Any]]:
        chunk_size = config.CHUNK_SIZE
        chunk_overlap = config.CHUNK_OVERLAP
        all_chunks = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]
            if not text:
                continue

            start = 0
            text_len = len(text)

            while start < text_len:
                end = start + chunk_size
                chunk_text = text[start:end]

                if end < text_len:
                    last_space = chunk_text.rfind(' ')
                    if last_space > chunk_size // 2:
                        end = start + last_space
                        chunk_text = text[start:end]

                chunk_text = chunk_text.strip()
                if chunk_text:
                    # Deterministic Chunk ID to prevent uncontrolled duplicate chunk generation
                    deterministic_id = f"{doc_id}_p{page_num}_c{global_chunk_idx}"
                    all_chunks.append({
                        "chunk_id": deterministic_id,
                        "text": chunk_text,
                        "metadata": {
                            "document_id": doc_id,
                            "filename": filename,
                            "original_filename": filename,
                            "product_id": product_id,
                            "page_number": page_num,
                            "chunk_index": global_chunk_idx,
                            "document_type": doc_type
                        }
                    })
                    global_chunk_idx += 1

                start += (chunk_size - chunk_overlap)

        return all_chunks

