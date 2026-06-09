import asyncio
from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PDFService:

    @staticmethod
    
    async def extract_text(pdf_path: Path) -> str:
        try:
          
            #asyncio.to thread () to push the heavy PDF reading to thread
            reader = await asyncio.to_thread(PdfReader, pdf_path)
        
            text_pages = []

            for page_number, page in enumerate(reader.pages):
                page_text = page.extract_text()

                if page_text and page_text.strip():
                    text_pages.append(page_text + "\n")
                    
                    logger.info(f"Processed page {page_number + 1} successfully")
                else:
                
                    logger.warning(f"Page {page_number + 1} is empty or scanned image")

            # Join the list together at the very end in a high-performance O(N) operation
            extracted_text = "".join(text_pages)

            if not extracted_text.strip():
                raise ValueError("PDF extraction yielded zero text. The file might be a scanned image or corrupted.")

            return extracted_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise
