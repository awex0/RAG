from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PDFService:

    @staticmethod
    def extract_text(pdf_path: Path) -> tuple[bool, str]:
        """
        Extract all text from a PDF file.
        """

        try:
            reader = PdfReader(pdf_path)

            extracted_text = ""

            for page_number, page in enumerate(reader.pages):

                page_text = page.extract_text()

                if page_text:
                    extracted_text += page_text + "\n"

                logger.info(f"Processed page {page_number + 1}")

            return True, extracted_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return False , f"PDF extraction failed: {e}"

        