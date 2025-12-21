"""File processing utilities."""
import PyPDF2
import docx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes different file types to extract text."""
    
    @staticmethod
    def extract_text(file_path: str, file_extension: str) -> Optional[str]:
        """
        Extract text from various file types.
        
        Args:
            file_path: Path to file
            file_extension: File extension (.txt, .pdf, .docx, etc.)
        
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            if file_extension.lower() in ['.txt', '.csv', '.log', '.md']:
                return FileProcessor._extract_text_file(file_path)
            elif file_extension.lower() == '.pdf':
                return FileProcessor._extract_pdf(file_path)
            elif file_extension.lower() in ['.docx', '.doc']:
                return FileProcessor._extract_docx(file_path)
            else:
                # Try as text file
                return FileProcessor._extract_text_file(file_path)
        
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return None
    
    @staticmethod
    def _extract_text_file(file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return '\n'.join(text)
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = docx.Document(file_path)
        text = []
        
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        
        return '\n'.join(text)


file_processor = FileProcessor()
