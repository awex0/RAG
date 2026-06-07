from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PDFService:

    @staticmethod
    # BUG: this method is not async
    # FastAPI runs on async event loop
    # sync call will block all requests
    # wrap it with asyncio.to_thread()
    # make the def async instead
    def extract_text(pdf_path: Path) -> str:

        # this comment says nothing useful
        # reader already tells us what happens
        # delete comments that repeat the code
        try:
            reader = PdfReader(pdf_path)

            # using string is the wrong choice
            # += creates a new string each time
            # gets slower with every page
            # use a list then join at end
            extracted_text = ""

            for page_number, page in enumerate(reader.pages):
                page_text = page.extract_text()

                if page_text:
                    # += in a loop is O(n squared)
                    # 500 pages means 500 new strings
                    # use pages.append(page_text) instead
                    extracted_text += page_text + "\n"

                # log is outside the if block
                # logs even when page has no text
                # move it inside the if block
                # add a warning for empty pages
                logger.info(f"Processed page {page_number + 1}")

            # empty string means scanned PDF
            # no error raised, caller gets nothing
            # add a check: if not extracted_text
            # raise ValueError with clear message
            return extracted_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise


# BUG: class has only static methods
# no reason to create an instance here
# call it directly: PDFService.extract_text()
# or remove @staticmethod and use self
# pick one pattern and stick to it
pdf_service = PDFService()

# BUG: this service is never used
# file_service.py ignores PDFs completely
# uploaded PDF text is never extracted
# wire it in process_file_upload()
# check content_type == application/pdf
