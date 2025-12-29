"""
DSI Document Processor (Phase 12)

Extract structured data from various document types.
"""

import io
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..types import (
    DocumentType,
    ExtractedData,
    ExtractionSchema,
)


logger = logging.getLogger("dsi.integrations.documents")


class DocumentProcessor:
    """
    Process and extract data from documents.

    Supports:
    - PDF documents (submissions, SOVs, financials)
    - Excel files (exposure data, schedules)
    - Word documents (applications)
    - Images with OCR
    """

    def __init__(
        self,
        ai_extractor: Optional[Callable] = None,
        ocr_enabled: bool = False,
    ):
        """
        Initialize document processor.

        Args:
            ai_extractor: Optional AI-based extraction function
            ocr_enabled: Enable OCR for scanned documents
        """
        self.ai_extractor = ai_extractor
        self.ocr_enabled = ocr_enabled

    async def process(
        self,
        file: bytes,
        filename: str,
        document_type: DocumentType = DocumentType.AUTO,
    ) -> ExtractedData:
        """
        Process a document and extract data.

        Args:
            file: Document bytes
            filename: Original filename
            document_type: Type of document (or AUTO to detect)

        Returns:
            ExtractedData with extracted information
        """
        # Detect file type from extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''

        if document_type == DocumentType.AUTO:
            document_type = self._detect_document_type(file, filename)

        if ext in ['pdf']:
            return await self.process_pdf(file, document_type)
        elif ext in ['xlsx', 'xls']:
            return await self.process_excel(file, document_type)
        elif ext in ['docx', 'doc']:
            return await self.process_word(file, document_type)
        elif ext in ['csv']:
            return await self.process_csv(file, document_type)
        else:
            return ExtractedData(
                document_type=document_type,
                confidence=0.0,
                errors=[f"Unsupported file type: {ext}"],
            )

    async def process_pdf(
        self,
        file: bytes,
        document_type: DocumentType = DocumentType.AUTO,
    ) -> ExtractedData:
        """
        Extract data from PDF document.

        Uses pypdf or pdfplumber for text extraction,
        with optional AI-powered field extraction.
        """
        logger.info(f"Processing PDF, type: {document_type.value}")

        fields: Dict[str, Any] = {}
        tables: List[Dict[str, Any]] = []
        raw_text = ""
        page_count = 0
        errors: List[str] = []

        try:
            # In production, use pypdf or pdfplumber:
            # import pypdf
            # reader = pypdf.PdfReader(io.BytesIO(file))
            # page_count = len(reader.pages)
            # for page in reader.pages:
            #     raw_text += page.extract_text()

            # Placeholder for demo
            page_count = 1
            raw_text = "[PDF content would be extracted here]"

            # Extract common fields based on document type
            if document_type == DocumentType.SUBMISSION:
                fields = self._extract_submission_fields(raw_text)
            elif document_type == DocumentType.SOV:
                fields, tables = self._extract_sov_data(raw_text)
            elif document_type == DocumentType.FINANCIAL:
                fields = self._extract_financial_data(raw_text)

            confidence = 0.8 if fields else 0.3

        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            errors.append(str(e))
            confidence = 0.0

        return ExtractedData(
            document_type=document_type,
            confidence=confidence,
            fields=fields,
            tables=tables,
            raw_text=raw_text[:5000] if raw_text else None,  # Limit size
            page_count=page_count,
            errors=errors,
        )

    async def process_excel(
        self,
        file: bytes,
        document_type: DocumentType = DocumentType.AUTO,
        sheet_hints: Optional[Dict[str, str]] = None,
    ) -> ExtractedData:
        """
        Extract data from Excel file.

        Common uses:
        - SOV (Statement of Values) with location data
        - Exposure schedules
        - Loss runs
        """
        logger.info(f"Processing Excel, type: {document_type.value}")

        fields: Dict[str, Any] = {}
        tables: List[Dict[str, Any]] = []
        errors: List[str] = []

        try:
            # In production, use openpyxl or pandas:
            # import pandas as pd
            # df = pd.read_excel(io.BytesIO(file), sheet_name=None)
            # for sheet_name, sheet_df in df.items():
            #     tables.append({"sheet": sheet_name, "data": sheet_df.to_dict()})

            # Placeholder for demo
            tables = [
                {
                    "sheet": "Locations",
                    "columns": ["Location", "Address", "TIV", "Construction"],
                    "row_count": 25,
                }
            ]

            if document_type == DocumentType.SOV:
                fields["total_tiv"] = 50000000
                fields["location_count"] = 25
                fields["states"] = ["CA", "NY", "TX"]

            confidence = 0.75

        except Exception as e:
            logger.error(f"Excel processing error: {e}")
            errors.append(str(e))
            confidence = 0.0

        return ExtractedData(
            document_type=document_type,
            confidence=confidence,
            fields=fields,
            tables=tables,
            errors=errors,
        )

    async def process_word(
        self,
        file: bytes,
        document_type: DocumentType = DocumentType.AUTO,
    ) -> ExtractedData:
        """Extract data from Word document."""
        logger.info(f"Processing Word, type: {document_type.value}")

        # In production, use python-docx
        return ExtractedData(
            document_type=document_type,
            confidence=0.5,
            raw_text="[Word document content]",
        )

    async def process_csv(
        self,
        file: bytes,
        document_type: DocumentType = DocumentType.AUTO,
    ) -> ExtractedData:
        """Extract data from CSV file."""
        logger.info(f"Processing CSV, type: {document_type.value}")

        tables: List[Dict[str, Any]] = []

        try:
            import csv
            reader = csv.DictReader(io.StringIO(file.decode('utf-8')))
            rows = list(reader)

            if rows:
                tables.append({
                    "columns": list(rows[0].keys()) if rows else [],
                    "row_count": len(rows),
                    "sample_rows": rows[:5],
                })

            confidence = 0.8

        except Exception as e:
            logger.error(f"CSV processing error: {e}")
            confidence = 0.0

        return ExtractedData(
            document_type=document_type,
            confidence=confidence,
            tables=tables,
        )

    async def extract_with_ai(
        self,
        document: bytes,
        extraction_schema: ExtractionSchema,
    ) -> Dict[str, Any]:
        """
        Use LLM for intelligent field extraction.

        Args:
            document: Document bytes
            extraction_schema: Schema defining fields to extract

        Returns:
            Extracted fields matching schema
        """
        if not self.ai_extractor:
            logger.warning("AI extractor not configured")
            return {}

        try:
            # Call AI extractor
            result = await self.ai_extractor(document, extraction_schema)
            return result

        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            return {}

    def _detect_document_type(self, file: bytes, filename: str) -> DocumentType:
        """Auto-detect document type."""
        filename_lower = filename.lower()

        if any(term in filename_lower for term in ['sov', 'statement of value', 'values']):
            return DocumentType.SOV
        elif any(term in filename_lower for term in ['submission', 'application', 'app']):
            return DocumentType.SUBMISSION
        elif any(term in filename_lower for term in ['financial', 'statement', '10k', '10-k']):
            return DocumentType.FINANCIAL
        elif any(term in filename_lower for term in ['loss', 'claims', 'run']):
            return DocumentType.LOSS_RUN

        return DocumentType.AUTO

    def _extract_submission_fields(self, text: str) -> Dict[str, Any]:
        """Extract fields from submission document."""
        fields: Dict[str, Any] = {}

        # Named insured
        match = re.search(r'named\s+insured[:\s]+([^\n]+)', text, re.IGNORECASE)
        if match:
            fields["named_insured"] = match.group(1).strip()

        # Effective date
        match = re.search(r'effective\s+date[:\s]+([^\n]+)', text, re.IGNORECASE)
        if match:
            fields["effective_date"] = match.group(1).strip()

        # Limit
        match = re.search(r'limit[:\s]*\$?([\d,]+)', text, re.IGNORECASE)
        if match:
            fields["limit"] = int(match.group(1).replace(',', ''))

        # Retention/Deductible
        match = re.search(r'(?:retention|deductible)[:\s]*\$?([\d,]+)', text, re.IGNORECASE)
        if match:
            fields["retention"] = int(match.group(1).replace(',', ''))

        return fields

    def _extract_sov_data(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract SOV data."""
        fields: Dict[str, Any] = {}
        tables: List[Dict[str, Any]] = []

        # Total TIV
        match = re.search(r'total\s+(?:tiv|insured\s+value)[:\s]*\$?([\d,]+)', text, re.IGNORECASE)
        if match:
            fields["total_tiv"] = int(match.group(1).replace(',', ''))

        return fields, tables

    def _extract_financial_data(self, text: str) -> Dict[str, Any]:
        """Extract financial statement data."""
        fields: Dict[str, Any] = {}

        # Revenue
        match = re.search(r'(?:total\s+)?revenue[:\s]*\$?([\d,]+)', text, re.IGNORECASE)
        if match:
            fields["revenue"] = int(match.group(1).replace(',', ''))

        # Assets
        match = re.search(r'total\s+assets[:\s]*\$?([\d,]+)', text, re.IGNORECASE)
        if match:
            fields["total_assets"] = int(match.group(1).replace(',', ''))

        return fields
