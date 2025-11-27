import os
import json
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader
from pptx import Presentation
import polib


class DocumentProcessor:
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Unified file reader for supported document types.

        Supported formats:
        .docx, .doc, .ppt, .pptx, .pdf (max 100 pages),
        .txt, .csv, .xlsx, .xls, .json, .xml,
        .srt, .xliff, .xlf, .po, .sdlxliff, .memoqxliff
        """

        ext = os.path.splitext(file_path)[1].lower()

        try:
            # ------------------- TEXT -------------------
            if ext == ".txt" or ext == ".srt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

            # ------------------- WORD (.docx) -------------------
            elif ext == ".docx":
                return DocumentProcessor.read_docx(file_path)

            # ------------------- WORD (.doc) -------------------
            elif ext == ".doc":
                return (
                    "⚠️ .doc (binary) files are not natively supported.\n"
                    "Please convert this file to .docx first for full extraction.\n\n"
                    + DocumentProcessor.read_binary(file_path)
                )

            # ------------------- PDF -------------------
            elif ext == ".pdf":
                return DocumentProcessor.read_pdf(file_path)

            # ------------------- EXCEL / CSV -------------------
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
                return df.to_string(index=False)

            elif ext == ".csv":
                df = pd.read_csv(file_path)
                return df.to_string(index=False)

            # ------------------- POWERPOINT -------------------
            elif ext == ".pptx":
                return DocumentProcessor.read_pptx(file_path)

            elif ext == ".ppt":
                return (
                    "⚠️ .ppt (binary) files are not natively supported.\n"
                    "Please convert this file to .pptx first for full extraction.\n\n"
                    + DocumentProcessor.read_binary(file_path)
                )

            # ------------------- JSON -------------------
            elif ext == ".json":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)

            # ------------------- XML / XLIFF -------------------
            elif ext in [".xml", ".xliff", ".xlf", ".sdlxliff", ".memoqxliff"]:
                return DocumentProcessor.read_xml_or_xliff(file_path)

            # ------------------- PO FILES -------------------
            elif ext == ".po":
                return DocumentProcessor.read_po(file_path)

            else:
                return f"⚠️ Unsupported file format: {ext}"

        except Exception as e:
            return f"⚠️ Error reading file {file_path}: {str(e)}"

    # ---------- Individual Readers ----------

    @staticmethod
    def read_docx(path: str) -> str:
        doc = Document(path)
        content = []

        for para in doc.paragraphs:
            content.append(para.text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    content.append(cell.text)

        return "\n".join(content)

    @staticmethod
    def read_pdf(path: str) -> str:
        reader = PdfReader(path)
        content = []

        max_pages = min(len(reader.pages), 100)

        for i in range(max_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                content.append(page_text)

        return "\n".join(content)

    @staticmethod
    def read_pptx(path: str) -> str:
        prs = Presentation(path)
        content = []

        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        content.append(paragraph.text)

        return "\n".join(content)

    @staticmethod
    def read_xml_or_xliff(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        soup = BeautifulSoup(raw, "xml")

        texts = []

        # Extract <source> and <target> text for XLIFF
        for tag in soup.find_all(["source", "target"]):
            if tag.string:
                texts.append(tag.string)

        # Fallback: if not XLIFF, return raw XML
        if not texts:
            return raw

        return "\n".join(texts)

    @staticmethod
    def read_po(path: str) -> str:
        po = polib.pofile(path)
        content = []

        for entry in po:
            if entry.msgid:
                content.append(entry.msgid)
            if entry.msgstr:
                content.append(entry.msgstr)

        return "\n".join(content)

    @staticmethod
    def read_binary(path: str) -> str:
        """
        Fallback for unsupported binary formats (e.g. .doc, .ppt)
        Just reads raw bytes and decodes best-effort.
        """
        with open(path, "rb") as f:
            raw = f.read()

        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return str(raw)


class TerminologyLoader:
    @staticmethod
    def load_glossary(path: str) -> str:
        """
        Glossary loader supporting CSV, XLSX, JSON, XML and PO.
        """
        ext = os.path.splitext(path)[1].lower()

        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
            return df.to_string(index=False)

        elif ext == ".csv":
            df = pd.read_csv(path)
            return df.to_string(index=False)

        elif ext in [".json"]:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)

        elif ext in [".xml", ".xliff", ".xlf", ".sdlxliff", ".memoqxliff"]:
            return DocumentProcessor.read_xml_or_xliff(path)

        elif ext == ".po":
            return DocumentProcessor.read_po(path)

        else:
            return f"Unsupported glossary format: {ext}"
