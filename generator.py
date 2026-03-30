"""
Style Guide Generator — Multi-Pass Architecture
=================================================
Phase 1: Document preprocessing (metadata extraction)
Phase 2: Section-by-section generation with full document context
Phase 3: Self-review and gap-filling pass
"""

import json
import logging
from typing import List, Optional, Dict

from text_utils import DocumentProcessor, TerminologyLoader
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════

PREPROCESSING_PROMPT = """You are a document metadata extraction specialist.
Analyze the provided document content and extract structured metadata.

Return ONLY valid JSON with no markdown formatting:
{
    "detected_domain": "primary industry/domain of the document",
    "content_type": "marketing | technical | legal | medical | financial | general",
    "terminology_density": "low | medium | high",
    "key_entities": {
        "companies": ["list of company names found"],
        "products": ["list of product/brand names found"],
        "people": ["list of person names found"],
        "places": ["list of geographic locations found"]
    },
    "measurements_found": ["list of specific numbers, dates, units found in the document"],
    "date_formats_found": ["list of date format patterns found, e.g. DD.MM.YYYY"],
    "number_formats_found": ["list of number format patterns, e.g. 1.234,56 (German)"],
    "abbreviations_found": ["list of abbreviations/acronyms found"],
    "formatting_patterns": "description of document formatting (tables, lists, headers)",
    "register": "formal | semi-formal | informal | mixed",
    "estimated_word_count": 0
}
"""

SYSTEM_PROMPT_MAIN = """You are an expert Localization Architect and Linguist working for a professional
translation agency. Your task is to write a comprehensive, detailed, and production-ready
Translation/Localization Style Guide based on the provided source documents.

CRITICAL QUALITY REQUIREMENTS:
- Every recommendation MUST be grounded in the actual source document content
- Include REAL examples extracted from the source text, not generic placeholders
- Cite actual terminology, measurements, dates, and numbers found in the document
- Be specific about formatting rules based on actual document formatting patterns
- Provide actionable guidance that a translator can immediately apply
- RESPECT THE WORD LIMIT specified in the user prompt — be concise but comprehensive
- Maximize information density: cover ALL topics but avoid verbose explanations
- Use tables, compact lists, and terse phrasing to fit maximum scope into limited space

REQUIRED STRUCTURE — You MUST include ALL of the following sections with substantial content:

1. SCOPE & PURPOSE
   - Document scope and objectives
   - Content type classification
   - Intended use of translations
   - Version control and update procedures

2. TARGET AUDIENCE PROFILE
   - Demographics and expertise level
   - Reading behavior patterns
   - Cultural sensitivities and regional considerations
   - Accessibility requirements

3. DOMAIN & CONTEXT
   - Primary industry/domain classification
   - Subject matter complexity assessment
   - Relevant standards and regulatory frameworks
   - Reference materials and authoritative sources

4. LANGUAGE SPECIFICATIONS & STYLE
   - Target language variants/dialects
   - Language register and formality level
   - Voice (active/passive preferences)
   - Person and form of address
   - Sentence length and complexity guidelines
   - DOs and DON'Ts with real examples from the source
   - Stylistic examples showing correct vs incorrect translations

5. GENDER & INCLUSIVITY
   - Gender-neutral language strategy per target language
   - Pronoun usage rules
   - Inclusive language guidelines
   - Practical examples for each target language

6. TERMINOLOGY & DO NOT TRANSLATE (DNT)
   - Categorized terminology list (minimum 20 terms extracted from the document)
   - Term preferences and forbidden alternatives
   - Acronym handling rules (expand on first use, etc.)
   - Complete DNT list: brand names, product names, variables, placeholders, tags
   - Named entities with translation/non-translation decisions
   - Termbase sources and management procedures

7. FORMATTING & LOCALE
   - Date format rules with actual conversion examples from the document
   - Number format rules with actual conversion examples
   - Unit and measurement conversion rules
   - Currency handling
   - Quotation mark styles per target language
   - Bullet and list formatting
   - Capitalization rules
   - Punctuation differences

8. SPATIAL & VISUAL CONSIDERATIONS
   - Text expansion/contraction expectations per language pair
   - UI and layout constraints
   - Truncation rules and character limits
   - Embedded text in images
   - Screenshot and UI element localization
   - Culturally sensitive imagery notes

9. QUALITY ASSURANCE & RESOURCES
   QA Tools: List specific QA tools and checks (CAT tool QA, terminology verification,
   spell-check, number/date validation, consistency checker, technical accuracy review)
   Thresholds: Define explicit pass/fail thresholds:
   - Critical errors: 0 tolerance
   - Major errors: maximum 2 per 1,000 words
   - Minor errors: maximum 5 per 1,000 words
   - Technical specifications: 100% accuracy required
   Standard Glossaries: List 3-5 concrete reference resources relevant to the domain
   Risk Assessment: Key translation challenges and mitigation strategies
   Resource Qualifications: Required translator expertise, tools, and experience level

OUTPUT FORMAT:
- Write as continuous text with numbered headings and sub-headings
- Do NOT output JSON or use markdown code fences
- Use **bold** for emphasis where needed
- Use bullet points (- ) for lists
- Include real examples from the source text wherever possible

LANGUAGE: Write the style guide in English.
"""

REVIEW_PROMPT = """You are a Quality Assurance specialist reviewing a Translation Style Guide.

Your task is to review the style guide below and identify any gaps, inconsistencies, or
areas where the guide could be more specific or actionable.

CHECK FOR:
1. COMPLETENESS: Are all 9 required sections present with substantial content?
2. SPECIFICITY: Does each section contain real examples from the source document?
3. TERMINOLOGY: Are there at least 20 categorized terms? Are DNT items listed?
4. MEASUREMENTS: Are date/number/unit conversion rules concrete with examples?
5. CONSISTENCY: Are recommendations consistent across sections?
6. ACTIONABILITY: Can a translator immediately apply this guidance?
7. QA SECTION: Does it include specific tools, thresholds, and glossary references?

OUTPUT: Write ONLY the missing or improved content that should be APPENDED to the guide.
If sections need enhancement, write the enhanced version of those sections.
If everything is complete, write "REVIEW COMPLETE — No gaps identified."

Do NOT repeat content that is already adequate. Only output additions and improvements.
"""

# ═══════════════════════════════════════════════════════════════════
# SECTION-SPECIFIC PROMPTS (for multi-pass generation)
# ═══════════════════════════════════════════════════════════════════

SECTION_PROMPTS = {
    "1_scope": """Write Section 1 (SCOPE & PURPOSE) and Section 2 (TARGET AUDIENCE PROFILE).
Include: document scope, content type, intended use, audience demographics, expertise level,
reading behavior, cultural sensitivities. Base all content on the actual source document.""",

    "2_domain_language": """Write Section 3 (DOMAIN & CONTEXT) and Section 4 (LANGUAGE SPECIFICATIONS & STYLE).
Include: industry classification, complexity assessment, standards/frameworks, target dialects,
register, voice, form of address, DOs/DON'Ts with real examples, stylistic examples.
Extract specific language patterns from the source document.""",

    "3_gender_terminology": """Write Section 5 (GENDER & INCLUSIVITY) and Section 6 (TERMINOLOGY & DNT).
Include: gender-neutral strategy per target language, pronoun rules, inclusive language.
For terminology: extract and categorize AT LEAST 20 terms from the source document.
List ALL brand names, product names, abbreviations, and DNT items found.
Include term preferences with forbidden alternatives.""",

    "4_formatting_spatial": """Write Section 7 (FORMATTING & LOCALE) and Section 8 (SPATIAL & VISUAL CONSIDERATIONS).
Include: date format conversions with REAL examples from the document,
number format conversions with REAL examples, unit conversions, currency handling,
quotation marks per target language, expansion/contraction rates, UI constraints.
Cite actual numbers and dates found in the source document.""",

    "5_qa_resources": """Write Section 9 (QUALITY ASSURANCE & RESOURCES).
Include:
- QA Tools: specific tools and checks relevant to this content type
- Thresholds: explicit pass/fail criteria (critical 0, major 2/1000, minor 5/1000)
- Standard Glossaries: 3-5 domain-relevant reference resources
- Risk Assessment: key translation challenges with mitigation strategies
- Resource Qualifications: required translator expertise, domain experience, tools
This section must be detailed and actionable.""",
}


# ═══════════════════════════════════════════════════════════════════
# DETAIL LEVEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

DETAIL_LEVELS = {
    "comprehensive": {
        "label": "Comprehensive",
        "max_words": 5000,
        "section_tokens": 4000,     # tokens per section in multi-pass
        "single_pass_tokens": 16000,
        "review_tokens": 4000,
        "preprocessing_tokens": 2000,
        "word_instruction": "TARGET LENGTH: ~5000 words total. Be thorough but concise — maximize coverage per word.",
    },
    "standard": {
        "label": "Standard",
        "max_words": 3500,
        "section_tokens": 2800,
        "single_pass_tokens": 12000,
        "review_tokens": 2000,
        "preprocessing_tokens": 2000,
        "word_instruction": "TARGET LENGTH: ~3000-3500 words total. Be focused and concise — cover all sections but keep explanations brief. Use compact tables and short bullet points.",
    },
    "basic": {
        "label": "Basic",
        "max_words": 1500,
        "section_tokens": 1200,
        "single_pass_tokens": 5000,
        "review_tokens": 0,     # skip review for basic
        "preprocessing_tokens": 1500,
        "word_instruction": "TARGET LENGTH: ~1000-1500 words total. Be extremely concise — one paragraph per section, compact term lists, minimal examples. Prioritize actionable rules over explanations.",
    },
}


class StyleGuideGenerator:
    """
    Multi-pass style guide generator using Claude.

    Architecture:
    1. Preprocessing: Extract metadata, entities, terminology from source
    2. Generation: Section-by-section or single-pass guide creation
    3. Review: Self-review pass to fill gaps and improve quality (skipped for basic tier)
    """

    def __init__(self, api_key: str, provider: str = "anthropic", model: Optional[str] = None):
        self.provider = provider
        self.llm_client = LLMClient(provider, api_key, model_name=model)

    @staticmethod
    def _prepare_context(texts: List[str], max_chars: int = 500000) -> str:
        """
        Join multiple extracted texts with separators.
        With Sonnet 4.6's 1M context window at standard pricing,
        we can send much more content (500K chars ≈ 125K tokens).
        """
        joined = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join(t for t in texts if t.strip())
        if len(joined) > max_chars:
            return joined[:max_chars] + "\n\n...[TRUNCATED — Document exceeds 500K characters]..."
        return joined

    def _preprocess_document(self, combined_context: str) -> Dict:
        """
        Phase 1: Extract metadata from source document using a quick LLM call.
        Returns structured metadata for use in generation prompts.
        """
        logger.info("Phase 1: Preprocessing document for metadata extraction...")

        user_prompt = f"""Analyze this document and extract metadata.

DOCUMENT CONTENT (first 100,000 characters):
{combined_context[:100000]}

Return ONLY valid JSON as specified in the system prompt."""

        try:
            raw = self.llm_client.generate_preprocessing(PREPROCESSING_PROMPT, user_prompt)
            # Clean JSON
            if "```" in raw:
                import re
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
                if match:
                    raw = match.group(1)
            start = raw.find('{')
            if start != -1:
                raw = raw[start:]
            metadata = json.loads(raw)
            logger.info(f"Preprocessing complete: domain={metadata.get('detected_domain')}, "
                       f"entities={len(metadata.get('key_entities', {}).get('companies', []))} companies")
            return metadata
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}. Continuing without metadata.")
            return {}

    def _build_enriched_prompt(
        self,
        combined_context: str,
        source_lang: str,
        target_langs: List[str],
        project_name: str,
        pm_notes: Optional[str],
        glossary_text: Optional[str],
        metadata: Dict,
    ) -> str:
        """Build a rich user prompt incorporating preprocessing metadata."""
        target_desc = ", ".join(target_langs) if target_langs else "GENERIC (multiple possible target languages)"

        entities_section = ""
        if metadata.get("key_entities"):
            entities = metadata["key_entities"]
            entities_section = f"""
ENTITIES DETECTED IN DOCUMENT:
- Companies: {', '.join(entities.get('companies', ['None detected']))}
- Products: {', '.join(entities.get('products', ['None detected']))}
- People: {', '.join(entities.get('people', ['None detected']))}
- Places: {', '.join(entities.get('places', ['None detected']))}
"""

        measurements_section = ""
        if metadata.get("measurements_found"):
            measurements_section = f"""
MEASUREMENTS & NUMBERS FOUND IN DOCUMENT:
{chr(10).join('- ' + m for m in metadata['measurements_found'][:30])}
"""

        formats_section = ""
        if metadata.get("date_formats_found") or metadata.get("number_formats_found"):
            formats_section = f"""
FORMAT PATTERNS DETECTED:
- Date formats: {', '.join(metadata.get('date_formats_found', ['Not detected']))}
- Number formats: {', '.join(metadata.get('number_formats_found', ['Not detected']))}
"""

        abbreviations_section = ""
        if metadata.get("abbreviations_found"):
            abbreviations_section = f"""
ABBREVIATIONS & ACRONYMS FOUND:
{', '.join(metadata['abbreviations_found'][:30])}
"""

        return f"""PROJECT NAME: {project_name}
SOURCE LANGUAGE: {source_lang}
TARGET LANGUAGES: {target_desc}
DETECTED DOMAIN: {metadata.get('detected_domain', 'Not detected')}
CONTENT TYPE: {metadata.get('content_type', 'Not detected')}
REGISTER: {metadata.get('register', 'Not detected')}
ESTIMATED WORD COUNT: {metadata.get('estimated_word_count', 'Unknown')}
{entities_section}
{measurements_section}
{formats_section}
{abbreviations_section}
PROJECT MANAGER NOTES:
{pm_notes if pm_notes else "None provided."}

GLOSSARY / TERMBASE:
{glossary_text if glossary_text else "None provided."}

SOURCE DOCUMENT CONTENT:
{combined_context}

Write the full style guide now, following ALL 9 required sections described in the system prompt.
Every section must contain substantial, specific content grounded in the source document.
"""

    def _generate_multi_pass(
        self,
        combined_context: str,
        source_lang: str,
        target_langs: List[str],
        project_name: str,
        pm_notes: Optional[str],
        glossary_text: Optional[str],
        metadata: Dict,
        detail_level: str = "comprehensive",
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Phase 2: Generate style guide section by section.
        Each section gets the full document context + preprocessing metadata.
        """
        logger.info("Phase 2: Multi-pass section-by-section generation...")

        config = DETAIL_LEVELS.get(detail_level, DETAIL_LEVELS["comprehensive"])
        target_desc = ", ".join(target_langs) if target_langs else "GENERIC"

        base_context = f"""PROJECT: {project_name}
SOURCE LANGUAGE: {source_lang}
TARGET LANGUAGES: {target_desc}
DOMAIN: {metadata.get('detected_domain', 'General')}
CONTENT TYPE: {metadata.get('content_type', 'General')}

DOCUMENT METADATA:
{json.dumps(metadata, indent=2, ensure_ascii=False, default=str)}

GLOSSARY:
{glossary_text if glossary_text else "None provided."}

SOURCE DOCUMENT:
{combined_context}
"""

        section_keys = list(SECTION_PROMPTS.items())
        total_sections = len(section_keys)
        # Total steps: preprocess(done) + sections + review = sections + 1 (review)
        total_steps = total_sections + 1  # +1 for review step
        sections = []

        for idx, (section_key, section_instruction) in enumerate(section_keys):
            logger.info(f"  Generating section: {section_key}")

            if progress_callback:
                step = idx + 1  # 1-based (preprocess was step 0)
                pct = int((step / (total_steps + 1)) * 100)
                section_label = section_key.split("_", 1)[-1].replace("_", " ").title()
                progress_callback(pct, f"Generating section {step}/{total_sections}: {section_label}...")

            user_prompt = f"""{base_context}

{config['word_instruction']}
This is section {idx+1} of {total_sections}. Allocate words proportionally — approximately {config['max_words'] // total_sections} words for this section.

INSTRUCTION:
{section_instruction}

Write this section now with specific content grounded in the source document.
Use numbered headings, bullet points, and real examples from the document.
Be concise — every sentence must add value."""

            section_text = self.llm_client.generate_section(
                system_prompt=SYSTEM_PROMPT_MAIN,
                user_prompt=user_prompt,
                max_tokens=config["section_tokens"],
            )
            sections.append(section_text)

        # Combine sections
        header = f"""TRANSLATION / LOCALIZATION STYLE GUIDE
PROJECT: {project_name}
Source: {source_lang} → Target: {target_desc}
Generated by: AICONTEXT Style Guide Creator | Anova Translation

---

"""
        full_guide = header + "\n\n---\n\n".join(sections)
        return full_guide

    def _review_and_enhance(
        self,
        guide_text: str,
        combined_context: str,
        metadata: Dict,
        detail_level: str = "comprehensive",
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Phase 3: Self-review pass to identify and fill gaps.
        Skipped for 'basic' detail level.
        """
        config = DETAIL_LEVELS.get(detail_level, DETAIL_LEVELS["comprehensive"])

        # Skip review for basic tier
        if config["review_tokens"] == 0:
            logger.info("Phase 3: Skipped (basic tier — no review pass)")
            if progress_callback:
                progress_callback(95, "Finalizing style guide...")
            return guide_text

        logger.info("Phase 3: Self-review and gap-filling...")

        if progress_callback:
            progress_callback(85, "Reviewing and enhancing style guide...")

        user_prompt = f"""STYLE GUIDE TO REVIEW:
{guide_text}

ORIGINAL DOCUMENT METADATA:
{json.dumps(metadata, indent=2, ensure_ascii=False, default=str)}

ORIGINAL DOCUMENT (first 50,000 characters for reference):
{combined_context[:50000]}

Review the style guide above and provide any missing content or improvements."""

        additions = self.llm_client.generate_review(
            system_prompt=REVIEW_PROMPT,
            user_prompt=user_prompt,
        )

        if additions and "REVIEW COMPLETE" not in additions.upper():
            logger.info("Review found gaps — appending improvements.")
            guide_text += "\n\n---\n\nADDITIONAL NOTES & IMPROVEMENTS\n\n" + additions
        else:
            logger.info("Review complete — no gaps identified.")

        return guide_text

    def create_guide_text(
        self,
        file_paths: List[str],
        source_lang: str,
        target_langs: List[str],
        project_name: str,
        pm_notes: Optional[str] = None,
        glossary_path: Optional[str] = None,
        multi_pass: bool = True,
        detail_level: str = "comprehensive",
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Main entry point for style guide generation.

        Args:
            file_paths: List of source document file paths
            source_lang: Source language code
            target_langs: List of target language codes
            project_name: Project name
            pm_notes: Optional project manager notes
            glossary_path: Optional path to glossary file
            multi_pass: If True, use section-by-section generation (recommended)
            detail_level: One of 'comprehensive', 'standard', 'basic'
            progress_callback: Optional callable(percent: int, message: str)
        """
        config = DETAIL_LEVELS.get(detail_level, DETAIL_LEVELS["comprehensive"])

        logger.info("Starting style guide generation...")
        logger.info(f"Source: {source_lang}, Targets: {target_langs or 'GENERIC'}, Project: {project_name}")
        logger.info(f"Mode: {'multi-pass' if multi_pass else 'single-pass'}, Detail: {detail_level} (~{config['max_words']} words)")

        if progress_callback:
            progress_callback(2, "Reading source documents...")

        # Read all source documents
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
        logger.info(f"Combined context: {len(combined_context)} characters")

        # Load glossary if provided
        glossary_text: Optional[str] = None
        if glossary_path:
            logger.info(f"Loading glossary from: {glossary_path}")
            glossary_text = TerminologyLoader.load_glossary(glossary_path)

        # Phase 1: Preprocess
        if progress_callback:
            progress_callback(5, "Preprocessing document (extracting metadata)...")
        metadata = self._preprocess_document(combined_context)

        if progress_callback:
            progress_callback(15, "Metadata extraction complete. Starting generation...")

        if multi_pass:
            # Phase 2: Multi-pass generation
            guide_text = self._generate_multi_pass(
                combined_context, source_lang, target_langs,
                project_name, pm_notes, glossary_text, metadata,
                detail_level=detail_level,
                progress_callback=progress_callback,
            )
            # Phase 3: Review
            guide_text = self._review_and_enhance(
                guide_text, combined_context, metadata,
                detail_level=detail_level,
                progress_callback=progress_callback,
            )
        else:
            # Single-pass fallback (faster, cheaper, lower quality)
            if progress_callback:
                progress_callback(20, "Generating style guide (single-pass)...")
            user_prompt = self._build_enriched_prompt(
                combined_context, source_lang, target_langs,
                project_name, pm_notes, glossary_text, metadata,
            )
            # Add word limit instruction to single-pass prompt
            user_prompt += f"\n\n{config['word_instruction']}"
            guide_text = self.llm_client.generate_style_guide_text(
                SYSTEM_PROMPT_MAIN, user_prompt,
                max_tokens=config["single_pass_tokens"],
            )

        if progress_callback:
            progress_callback(100, "Style guide generation complete!")

        logger.info("Style guide generation complete.")
        return guide_text
