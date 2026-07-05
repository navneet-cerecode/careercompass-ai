"""
Resume Parser Service.

Chooses the correct parser
based on file extension.
"""

from pathlib import Path

from services.resume.pdf_parser import PDFParser
from services.resume.docx_parser import DOCXParser
from services.resume.txt_parser import TXTParser


class ResumeParserService:

    def __init__(self):

        self.parsers = {
            ".pdf": PDFParser(),
            ".docx": DOCXParser(),
            ".txt": TXTParser(),
        }

    def parse(
        self,
        file_path: str,
    ) -> str:

        # Remove accidental quotes and whitespace
        file_path = file_path.strip().strip('"').strip("'")

        extension = Path(file_path).suffix.lower()

        parser = self.parsers.get(extension)

        if parser is None:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        return parser.parse(file_path)