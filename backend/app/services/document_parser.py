import csv
import io
import os
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import pypdf
import docx
import openpyxl

logger = logging.getLogger(__name__)


@dataclass
class ParsedChunk:
    chunk_text: str
    page_number: Optional[int] = 1
    section: Optional[str] = "General"
    chunk_type: str = "text"  # "text" | "table" | "protocol"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentParserService:
    """
    Parser service supporting PDF, DOCX, TXT, CSV, and XLSX healthcare documents.
    Extracts text, sections, page numbers, and preserves table name, row, column, and values.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}

    def __init__(self, target_chunk_size: int = 600, overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def parse_file(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        """
        Detect file format by extension and parse into structured chunks.
        """
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        if ext == ".pdf":
            return self._parse_pdf(file_bytes, filename)
        elif ext == ".docx":
            return self._parse_docx(file_bytes, filename)
        elif ext == ".txt":
            return self._parse_txt(file_bytes, filename)
        elif ext == ".csv":
            return self._parse_csv(file_bytes, filename)
        elif ext == ".xlsx":
            return self._parse_xlsx(file_bytes, filename)
        else:
            raise ValueError(f"Unhandled file extension: {ext}")

    # =========================================================================
    # PDF Parser
    # =========================================================================
    def _parse_pdf(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        chunks: List[ParsedChunk] = []
        stream = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(stream)
        current_section = "Overview"

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            if not raw_text.strip():
                continue

            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            buffer = []

            for line in lines:
                # Detect section headings (e.g., "Section 1", "Protocol:", "1. Guideline", etc.)
                if self._is_heading(line):
                    if buffer:
                        text_block = "\n".join(buffer)
                        chunks.extend(self._chunk_text(text_block, page_number=page_num, section=current_section))
                        buffer = []
                    current_section = line[:100]
                else:
                    buffer.append(line)

            if buffer:
                text_block = "\n".join(buffer)
                chunks.extend(self._chunk_text(text_block, page_number=page_num, section=current_section))

        if not chunks:
            # Fallback if text was sparse
            chunks.append(ParsedChunk(
                chunk_text=f"Empty or non-extractable PDF document: {filename}",
                page_number=1,
                section="General",
                chunk_type="text"
            ))

        return chunks

    # =========================================================================
    # DOCX Parser
    # =========================================================================
    def _parse_docx(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        chunks: List[ParsedChunk] = []
        stream = io.BytesIO(file_bytes)
        doc = docx.Document(stream)
        current_section = "General Clinical Guidance"
        paragraph_buffer = []

        # Process document elements in order: paragraphs and tables
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            # Check if paragraph has heading style or looks like a heading
            if p.style and "Heading" in p.style.name or self._is_heading(text):
                if paragraph_buffer:
                    block = "\n".join(paragraph_buffer)
                    chunks.extend(self._chunk_text(block, page_number=1, section=current_section))
                    paragraph_buffer = []
                current_section = text[:100]
            else:
                paragraph_buffer.append(text)

        if paragraph_buffer:
            block = "\n".join(paragraph_buffer)
            chunks.extend(self._chunk_text(block, page_number=1, section=current_section))

        # Process Word tables preserving Table Name, Row, Column, Value
        table_name_base = os.path.splitext(filename)[0]
        for tbl_idx, table in enumerate(doc.tables):
            table_name = f"{table_name_base} - Table {tbl_idx + 1}"
            table_chunks = self._extract_table_rows(
                rows_data=[[cell.text.strip() for cell in row.cells] for row in table.rows],
                table_name=table_name,
                section=f"{current_section} (Table {tbl_idx + 1})",
                page_number=1,
            )
            chunks.extend(table_chunks)

        return chunks

    # =========================================================================
    # TXT Parser
    # =========================================================================
    def _parse_txt(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1", errors="replace")

        lines = [l.strip() for l in content.splitlines()]
        chunks: List[ParsedChunk] = []
        current_section = "General Clinical Notes"
        buffer = []
        page_approx = 1
        line_count = 0

        for line in lines:
            if not line:
                continue
            line_count += 1
            if line_count % 40 == 0:
                page_approx += 1

            if self._is_heading(line):
                if buffer:
                    text_block = "\n".join(buffer)
                    chunks.extend(self._chunk_text(text_block, page_number=page_approx, section=current_section))
                    buffer = []
                current_section = line[:100]
            else:
                buffer.append(line)

        if buffer:
            text_block = "\n".join(buffer)
            chunks.extend(self._chunk_text(text_block, page_number=page_approx, section=current_section))

        return chunks

    # =========================================================================
    # CSV Parser (Preserving Table Name, Row, Column, Value)
    # =========================================================================
    def _parse_csv(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        try:
            text_content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = file_bytes.decode("latin-1", errors="replace")

        stream = io.StringIO(text_content)
        reader = list(csv.reader(stream))
        if not reader:
            return []

        table_name = os.path.splitext(filename)[0]
        return self._extract_table_rows(
            rows_data=reader,
            table_name=table_name,
            section=f"Dataset: {table_name}",
            page_number=1,
        )

    # =========================================================================
    # XLSX Parser (Preserving Table Name, Row, Column, Value)
    # =========================================================================
    def _parse_xlsx(self, file_bytes: bytes, filename: str) -> List[ParsedChunk]:
        stream = io.BytesIO(file_bytes)
        wb = openpyxl.load_workbook(stream, data_only=True)
        chunks: List[ParsedChunk] = []

        for sheet_idx, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            raw_rows = []
            for row in ws.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                    raw_rows.append(cleaned_row)

            if raw_rows:
                table_chunks = self._extract_table_rows(
                    rows_data=raw_rows,
                    table_name=f"{filename} [{sheet_name}]",
                    section=f"Spreadsheet Sheet: {sheet_name}",
                    page_number=sheet_idx + 1,
                )
                chunks.extend(table_chunks)

        return chunks

    # =========================================================================
    # Table Extractor - Preserves Table Name, Row, Column, Value
    # =========================================================================
    def _extract_table_rows(
        self,
        rows_data: List[List[str]],
        table_name: str,
        section: str,
        page_number: int = 1,
    ) -> List[ParsedChunk]:
        """
        Converts tabular data into structured chunks preserving:
        - table name
        - row number
        - column name
        - cell value
        """
        if not rows_data:
            return []

        # Row 0 treated as headers
        headers = [h if h else f"Column_{idx+1}" for idx, h in enumerate(rows_data[0])]
        table_chunks: List[ParsedChunk] = []

        # Batch rows (e.g., 3-5 rows per chunk for cohesive clinical context)
        batch_size = 4
        current_batch = []
        batch_start_row = 1

        for row_idx, row in enumerate(rows_data[1:], start=1):
            # Format row preserving Table Name, Row, Column, Value
            col_val_pairs = []
            for col_idx, col_name in enumerate(headers):
                val = row[col_idx] if col_idx < len(row) else ""
                col_val_pairs.append(f"{col_name}={val}")

            row_str = f"Row {row_idx}: " + " | ".join(col_val_pairs)
            current_batch.append(row_str)

            if len(current_batch) >= batch_size:
                chunk_content = (
                    f"[Table: {table_name}]\n"
                    f"Columns: {', '.join(headers)}\n"
                    + "\n".join(current_batch)
                )
                table_chunks.append(ParsedChunk(
                    chunk_text=chunk_content,
                    page_number=page_number,
                    section=section,
                    chunk_type="table",
                    metadata={
                        "table_name": table_name,
                        "start_row": batch_start_row,
                        "end_row": row_idx,
                        "columns": headers,
                    }
                ))
                current_batch = []
                batch_start_row = row_idx + 1

        if current_batch:
            chunk_content = (
                f"[Table: {table_name}]\n"
                f"Columns: {', '.join(headers)}\n"
                + "\n".join(current_batch)
            )
            table_chunks.append(ParsedChunk(
                chunk_text=chunk_content,
                page_number=page_number,
                section=section,
                chunk_type="table",
                metadata={
                    "table_name": table_name,
                    "start_row": batch_start_row,
                    "end_row": len(rows_data) - 1,
                    "columns": headers,
                }
            ))

        return table_chunks

    # =========================================================================
    # Basic Text Chunking Algorithm
    # =========================================================================
    def _chunk_text(self, text: str, page_number: int, section: str) -> List[ParsedChunk]:
        """
        Splits text into chunks of target_chunk_size while respecting paragraph
        and sentence boundaries and maintaining chunk metadata.
        """
        text = text.strip()
        if not text:
            return []

        # If text is small enough, return as single chunk
        if len(text) <= self.target_chunk_size:
            return [ParsedChunk(
                chunk_text=text,
                page_number=page_number,
                section=section,
                chunk_type="text",
            )]

        chunks = []
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_chunk_paras = []
        current_len = 0

        for p in paragraphs:
            if current_len + len(p) > self.target_chunk_size and current_chunk_paras:
                chunk_str = "\n\n".join(current_chunk_paras)
                chunks.append(ParsedChunk(
                    chunk_text=chunk_str,
                    page_number=page_number,
                    section=section,
                    chunk_type="text",
                ))
                # Retain overlap if feasible
                current_chunk_paras = [p]
                current_len = len(p)
            else:
                current_chunk_paras.append(p)
                current_len += len(p)

        if current_chunk_paras:
            chunks.append(ParsedChunk(
                chunk_text="\n\n".join(current_chunk_paras),
                page_number=page_number,
                section=section,
                chunk_type="text",
            ))

        return chunks

    def _is_heading(self, line: str) -> bool:
        """Heuristic check if a line is a clinical section heading."""
        if not line or len(line) > 120:
            return False
        line_clean = line.strip()

        # Markdown headings
        if line_clean.startswith("#"):
            return True
        # "Section 1.2", "Part A", "Chapter 3", "Protocol:"
        if re.match(r"^(Section|Chapter|Appendix|Protocol|Guideline|Part)\s+[\d\w\.\:]+", line_clean, re.IGNORECASE):
            return True
        # "1.0 Title" or "1. Introduction"
        if re.match(r"^\d+(\.\d+)*\s+[A-Z]", line_clean):
            return True
        # All upper case short lines (e.g., "CLINICAL INDICATIONS", "DOSAGE AND ADMINISTRATION")
        if line_clean.isupper() and len(line_clean.split()) <= 8:
            return True
        # Ends with colon and short (e.g., "Contraindications and Warnings:")
        if line_clean.endswith(":") and len(line_clean.split()) <= 7:
            return True

        return False
