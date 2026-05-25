from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PDFService:

    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """
        Extract text from PDF pages.
        """

        try:
            reader = PdfReader(pdf_path)

            extracted_text = ""

            for page_number, page in enumerate(reader.pages):

                page_text = page.extract_text()

                if page_text:
                    extracted_text += page_text + "\n"

                logger.info(f"Processed page {page_number + 1}")

            return extracted_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise


pdf_service = PDFService()