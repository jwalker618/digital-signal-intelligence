# PDF document extractor

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import requests


@dataclass
class PDFContent:
    '''Extracted content from PDF'''

    url: str
    text: str
    metadata: Dict
    page_count: int
    file_size: int
    extraction_date: datetime


class PDFExtractor:
    '''
    Extracts text and metadata from PDF documents.

    Note: Requires PyPDF2 or pdfplumber for full functionality.
    Falls back to basic extraction if libraries not available.
    '''

    def __init__(self, timeout: int = 30):
        '''
        Initialize PDF extractor.

        Args:
            timeout: Download timeout in seconds
        '''
        self.timeout = timeout

        # Try to import PDF libraries
        self.pdf_library = self._detect_pdf_library()

    def _detect_pdf_library(self) -> str:
        '''Detect which PDF library is available'''
        try:
            import PyPDF2  # noqa: F401

            return 'pypdf2'
        except ImportError:
            pass

        try:
            import pdfplumber  # noqa: F401

            return 'pdfplumber'
        except ImportError:
            pass

        return 'none'

    def extract(self, pdf_url: str) -> Optional[PDFContent]:
        '''
        Extract content from PDF.

        Args:
            pdf_url: URL to PDF document

        Returns:
            PDFContent or None if extraction fails
        '''
        try:
            # Download PDF
            print(f'  📄 Downloading PDF: {pdf_url}')
            response = requests.get(pdf_url, timeout=self.timeout)
            response.raise_for_status()

            pdf_bytes = response.content
            file_size = len(pdf_bytes)

            # Extract based on available library
            if self.pdf_library == 'pypdf2':
                return self._extract_with_pypdf2(pdf_url, pdf_bytes, file_size)
            elif self.pdf_library == 'pdfplumber':
                return self._extract_with_pdfplumber(pdf_url, pdf_bytes, file_size)
            else:
                # Fallback: basic text extraction
                return self._extract_basic(pdf_url, pdf_bytes, file_size)

        except Exception as e:
            print(f'  ✗ Failed to extract PDF: {str(e)}')
            return None

    def _extract_with_pypdf2(
        self, url: str, pdf_bytes: bytes, file_size: int
    ) -> PDFContent:
        '''Extract using PyPDF2'''
        import PyPDF2

        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)

        # Extract text
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())

        text = '\n'.join(text_parts)

        # Extract metadata
        metadata = {}
        if reader.metadata:
            metadata = {
                key.replace('/', ''): str(value)
                for key, value in reader.metadata.items()
            }

        return PDFContent(
            url=url,
            text=text,
            metadata=metadata,
            page_count=len(reader.pages),
            file_size=file_size,
            extraction_date=datetime.now(),
        )

    def _extract_with_pdfplumber(
        self, url: str, pdf_bytes: bytes, file_size: int
    ) -> PDFContent:
        '''Extract using pdfplumber (more accurate)'''
        import pdfplumber

        pdf_file = io.BytesIO(pdf_bytes)

        with pdfplumber.open(pdf_file) as pdf:
            # Extract text
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            text = '\n'.join(text_parts)

            # Extract metadata
            metadata = pdf.metadata or {}

            return PDFContent(
                url=url,
                text=text,
                metadata=metadata,
                page_count=len(pdf.pages),
                file_size=file_size,
                extraction_date=datetime.now(),
            )

    def _extract_basic(self, url: str, pdf_bytes: bytes, file_size: int) -> PDFContent:
        '''Basic extraction (no library required, limited accuracy)'''
        # Very basic: just try to decode as text
        # This is a fallback and won't work well for most PDFs

        try:
            text = pdf_bytes.decode('utf-8', errors='ignore')
        except Exception:
            text = ''

        return PDFContent(
            url=url,
            text=text,
            metadata={'extraction_method': 'basic'},
            page_count=0,
            file_size=file_size,
            extraction_date=datetime.now(),
        )

    def find_sections(
        self, content: PDFContent, section_names: List[str]
    ) -> Dict[str, str]:
        '''
        Find specific sections in PDF content.

        Args:
            content: Extracted PDF content
            section_names: Section headers to find

        Returns:
            Dictionary mapping section names to content
        '''
        sections = {}

        text = content.text
        text_lower = text.lower()

        for section_name in section_names:
            section_lower = section_name.lower()

            # Find section start
            start_pos = text_lower.find(section_lower)
            if start_pos == -1:
                continue

            # Find next section (or end of document)
            end_pos = len(text)
            for other_section in section_names:
                if other_section != section_name:
                    other_pos = text_lower.find(
                        other_section.lower(), start_pos + len(section_lower)
                    )
                    if other_pos != -1 and other_pos < end_pos:
                        end_pos = other_pos

            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            sections[section_name] = section_content

        return sections

    def extract_tables(self, content: PDFContent) -> List[Dict]:
        '''
        Extract tables from PDF (requires pdfplumber).

        Args:
            content: Extracted PDF content

        Returns:
            List of tables as dictionaries
        '''
        if self.pdf_library != 'pdfplumber':
            print('  ⚠️  Table extraction requires pdfplumber library')
            return []

        # This would require re-downloading the PDF
        # Placeholder for future implementation
        return []

    def extract_metrics(
        self, content: PDFContent, metric_patterns: Dict[str, str]
    ) -> Dict[str, str]:
        '''
        Extract specific metrics using regex patterns.

        Args:
            content: Extracted PDF content
            metric_patterns: Dict mapping metric names to regex patterns

        Returns:
            Dictionary of extracted metrics
        '''
        metrics = {}

        for metric_name, pattern in metric_patterns.items():
            matches = re.findall(pattern, content.text, re.IGNORECASE)
            if matches:
                # Take first match
                metrics[metric_name] = matches[0]

        return metrics
