import os
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import json
from aes import AES

PLAINTEXT_FOLDER = 'plaintext_files'
CIPHERTEXT_FOLDER = 'ciphertext_files'
os.makedirs(PLAINTEXT_FOLDER, exist_ok=True)
os.makedirs(CIPHERTEXT_FOLDER, exist_ok=True)

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
    def save_pdf(text, output_path):
        """Save text as PDF file with proper text wrapping"""
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        
        width, height = letter
        margin = 72  # 1 inch margins
        y = height - margin
        x = margin
        font_size = 10
        line_height = font_size * 1.2
        
        # Set font
        c.setFont("Helvetica", font_size)
        
        # Split text into lines and handle page breaks
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                y -= line_height
                continue
                
            # Simple word-wrapping algorithm
            words = paragraph.split()
            line = ""
            
            for word in words:
                test_line = line + (" " if line else "") + word
                width_of_line = c.stringWidth(test_line, "Helvetica", font_size)
                
                if width_of_line <= (width - 2*margin):
                    line = test_line
                else:
                    c.drawString(x, y, line)
                    y -= line_height
                    line = word
                    
                    # Check if we need a new page
                    if y < margin:
                        c.showPage()
                        y = height - margin
                        c.setFont("Helvetica", font_size)
            
            # Draw the last line of the paragraph
            if line:
                c.drawString(x, y, line)
                y -= line_height * 1.5  # Extra space after paragraph
                
            # Check if we need a new page
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", font_size)
        
        c.save()
        
        # Create the final PDF
        packet.seek(0)
        new_pdf = PdfReader(packet)
        writer = PdfWriter()
        
        for page in range(len(new_pdf.pages)):
            writer.add_page(new_pdf.pages[page])
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

    @staticmethod
    def save_docx(text, output_path):
        """Save text as DOCX file with chunking for large documents"""
        doc = Document()
        
        # Process paragraphs
        for paragraph in text.split('\n'):
            if paragraph.strip():
                p = doc.add_paragraph()
                # Add text in smaller chunks to avoid memory issues
                chunk_size = 1000  # Adjust as needed
                for i in range(0, len(paragraph), chunk_size):
                    chunk = paragraph[i:i+chunk_size]
                    if i == 0:
                        p.add_run(chunk)
                    else:
                        p.add_run(chunk)
        
        doc.save(output_path)

    @staticmethod
    def get_file_extension(filename):
        """Get file extension in lowercase"""
        return os.path.splitext(filename)[1].lower()