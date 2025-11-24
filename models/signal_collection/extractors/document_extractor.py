# Generic document extractor that routes to specific extractors

from typing import Optional, Union

from .html_extractor import HTMLArticle, HTMLExtractor
from .pdf_extractor import PDFContent, PDFExtractor


class DocumentExtractor:
    '''
    Generic document extractor that routes to appropriate extractor
    '''

    def __init__(self, timeout: int = 30):
        '''
        Initialize document extractor.

        Args:
            timeout: Request timeout in seconds
        '''
        self.pdf_extractor = PDFExtractor(timeout=timeout)
        self.html_extractor = HTMLExtractor()

    def extract(
        self, url: str, content: str = None, content_type: str = None
    ) -> Optional[Union[PDFContent, HTMLArticle]]:
        '''
        Extract content from document.

        Args:
            url: Document URL
            content: Optional pre-fetched content
            content_type: Content type hint

        Returns:
            Extracted content or None
        '''
        # Determine document type
        if content_type:
            doc_type = self._get_type_from_content_type(content_type)
        else:
            doc_type = self._get_type_from_url(url)

        # Route to appropriate extractor
        if doc_type == 'pdf':
            return self.pdf_extractor.extract(url)
        elif doc_type == 'html':
            if content:
                return self.html_extractor.extract_article(content, url)
            else:
                # Would need to fetch content first
                return None
        else:
            return None

    def _get_type_from_url(self, url: str) -> str:
        '''Determine document type from URL'''
        url_lower = url.lower()

        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.doc', '.docx')):
            return 'word'
        elif url_lower.endswith(('.xls', '.xlsx')):
            return 'excel'
        else:
            return 'html'

    def _get_type_from_content_type(self, content_type: str) -> str:
        '''Determine document type from content-type header'''
        content_type_lower = content_type.lower()

        if 'pdf' in content_type_lower:
            return 'pdf'
        elif 'word' in content_type_lower or 'document' in content_type_lower:
            return 'word'
        elif 'excel' in content_type_lower or 'spreadsheet' in content_type_lower:
            return 'excel'
        elif 'html' in content_type_lower:
            return 'html'
        else:
            return 'unknown'
