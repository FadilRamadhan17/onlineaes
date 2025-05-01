import os
from PyPDF2 import PdfReader
from docx import Document

class FileHandler:
    @staticmethod
    def read_pdf(file):
        """Read content from PDF file"""
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def read_docx(file):
        """Read content from DOCX file"""
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
        
    @staticmethod
    def get_file_extension(filename):
        """Get file extension in lowercase"""
        return os.path.splitext(filename)[1].lower()