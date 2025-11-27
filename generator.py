import logging
from typing import List, Optional

from text_utils import DocumentProcessor, TerminologyLoader
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


SYSTEM_PROMPT_TEXT = """
You are an expert Localization Architect and Linguist.
Your task is to write a clear, well-structured Translation/Localization Style Guide
in plain text (headings and paragraphs), based on the provided source documents,
Project Manager notes, and terminology.

IMPORTANT:
- Do NOT output JSON.
- Do NOT use markdown code fences.
- Instead, write a human-readable guide with numbered sections and subsections.

REQUIRED STRUCTURE (EXAMPLE):
1. Scope & Purpose
2. Target Audience
3. Domain & Context
4. Language Specifications & Style
5. Gender & Inclusivity
6. Terminology & Do Not Translate
7. Formatting & Locale
8. Spatial & Visual Considerations
9. Quality Assurance & Resources

GUIDANCE:
- If specific target languages are provided, tailor your recommendations to that/those languages.
- If no specific target languages are given (GENERIC mode), write guidance that helps
  translators working from the source language into multiple common target languages,
  focusing on general principles but still using concrete examples from the source text.

In section 9 (Quality Assurance & Resources), you MUST include the following three lines
in this exact structure, filled with concrete, project-relevant content:

9. QA & Resources
QA Tools: list the concrete QA tools and checks to use (e.g. CAT tool with integrated QA,
terminology verification against approved glossary, spell-check and grammar verification,
number/date format validation, consistency checker, technical accuracy review).
Thresholds: define explicit thresholds for critical, major and minor errors
(e.g. critical errors: 0 tolerance; major errors: maximum 2 per 1,000 words; minor errors:
maximum 5 per 1,000 words; all technical specifications must achieve 100% accuracy).
Standard Glossaries: list 3–5 concrete reference resources (e.g. Microsoft Style Guide,
IEC Electropedia, ISO Online Browsing Platform, IATE, SAE International terminology, etc.).

You can add additional explanatory text under or around these lines if helpful, but the three
labels "QA Tools:", "Thresholds:" and "Standard Glossaries:" must be present and filled with
meaningful content.

Within all sections, you should:
- Describe tone, voice, and register.
- Explain how to handle terminology, acronyms, and DNT items.
- Explain how to handle dates, times, numbers, units, and lists.
- Provide concrete examples taken from the source text where useful.
- Keep the guide practical, concise, and ready for translators to use.

Write the full style guide as continuous text with headings and paragraphs.
"""


class StyleGuideGenerator:
    """
    Claude-only style guide generator.

    - Uses LLMClient (Claude) to produce a plain-text style guide.
    - No JSON / OpenAI path anymore.
    """

    def __init__(self, api_key: str, provider: str = "anthropic", model: Optional[str] = None):
        """
        provider is kept only to pass 'anthropic' / 'claude' into LLMClient.
        """
        self.provider = provider
        self.llm_client = LLMClient(provider, api_key, model_name=model)

    @staticmethod
    def _prepare_context(texts: List[str], max_chars: int = 16000) -> str:
        """
        Join multiple extracted texts with separators and hard truncate
        to avoid over-long prompts.
        """
        joined = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join(t for t in texts if t.strip())
        if len(joined) > max_chars:
            return joined[:max_chars] + "\n\n...[TRUNCATED]..."
        return joined

    def create_guide_text(
        self,
        file_paths: List[str],
        source_lang: str,
        target_langs: List[str],
        project_name: str,
        pm_notes: Optional[str] = None,
        glossary_path: Optional[str] = None,
    ) -> str:
        """
        Main entry point for Claude-only style guide generation.

        - Reads and concatenates content from file_paths.
        - Loads glossary text if provided.
        - Builds a rich user prompt.
        - Calls Claude via LLMClient and returns the guide text.
        """
        logger.info("Starting style guide (text) generation...")
        logger.info(f"Source language: {source_lang}")
        logger.info(f"Target languages: {target_langs if target_langs else 'GENERIC'}")
        logger.info(f"Project name: {project_name}")

        texts: List[str] = []
        for path in file_paths:
            logger.info(f"Reading file: {path}")
            content = DocumentProcessor.read_file(path)
            if content:
                texts.append(content)
            else:
                logger.warning(f"No content extracted from: {path}")

        if not texts:
            raise ValueError("No valid text could be extracted from the provided files.")

        combined_context = self._prepare_context(texts)

        glossary_text: Optional[str] = None
        if glossary_path:
            logger.info(f"Loading glossary from: {glossary_path}")
            glossary_text = TerminologyLoader.load_glossary(glossary_path)

        if target_langs:
            target_desc = ", ".join(target_langs)
        else:
            target_desc = "GENERIC (multiple possible target languages)"

        system_prompt = SYSTEM_PROMPT_TEXT

        user_prompt = f"""
PROJECT NAME: {project_name}

SOURCE LANGUAGE: {source_lang}
TARGET LANGUAGES: {target_desc}

PROJECT MANAGER NOTES:
{pm_notes if pm_notes else "None provided."}

GLOSSARY SAMPLE:
{glossary_text if glossary_text else "None provided."}

SOURCE DOCUMENT CONTENT SAMPLES:
{combined_context}

Write the full style guide now, following the required structure described in the system prompt.
"""

        logger.info("Calling Claude to generate style guide text...")
        guide_text = self.llm_client.generate_style_guide_text(system_prompt, user_prompt)
        logger.info("Received style guide text from Claude.")
        return guide_text
