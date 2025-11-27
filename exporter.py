import os
from typing import Optional

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from models import StyleGuide


class StyleGuideExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # ---------- JSON export for structured StyleGuide (kept for future use) ----------

    def export_json(self, style_guide: StyleGuide, filename: str) -> str:
        """
        Export a StyleGuide Pydantic model to JSON.
        (Not used in the current Claude-only workflow, but kept for completeness.)
        """
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            # Pydantic v2: no ensure_ascii argument
            f.write(style_guide.model_dump_json(indent=2))
        return path

    # ---------- DOCX export for structured StyleGuide (OpenAI path, not used now) ----------

    def export_docx(self, style_guide: StyleGuide, filename: str) -> str:
        """
        Export a structured StyleGuide (JSON/Pydantic) to a formatted DOCX.

        NOTE: This is primarily for the old OpenAI JSON workflow.
        Your current Claude-only flow uses export_plaintext_docx().
        """
        doc = Document()

        def add_title(text: str):
            title = doc.add_heading(text, level=0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        def add_section(title_text: str):
            doc.add_heading(title_text, level=1)

        def add_kv(label: str, value: Optional[str]):
            if not value:
                return
            p = doc.add_paragraph()
            run_label = p.add_run(f"{label}: ")
            run_label.bold = True
            run_value = p.add_run(value)
            run_value.font.size = Pt(10)

        # Header
        header = style_guide.header
        add_title(header.title)

        meta_p = doc.add_paragraph()
        meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta_p.add_run(f"Project: {header.project_name} | ").bold = True
        # header.target_languages is assumed to be a list in the latest models.py
        meta_p.add_run(
            f"Source: {header.source_language} → Target(s): {', '.join(header.target_languages)}\n"
        )
        meta_p.add_run(
            f"Version: {header.version} | Prepared by: {header.prepared_by} | Date: {header.creation_date}"
        )

        doc.add_paragraph()

        # 1. Scope & Audience
        add_section("1. Scope & Audience Profile")
        sp = style_guide.scope_purpose
        ta = style_guide.target_audience
        add_kv("Scope", sp.document_scope)
        add_kv("Content Type", sp.content_type)
        add_kv("Audience Demographics", ta.demographics)
        add_kv("Audience Expertise", ta.expertise_level)
        add_kv("Reading Behaviour", ta.reading_behaviour)
        add_kv("Cultural Sensitivities", ta.cultural_sensitivities)

        # 2. Domain & Context
        add_section("2. Domain & Context")
        dc = style_guide.domain_context
        add_kv("Industry", dc.industry)
        add_kv("References", dc.references)

        # 3. Language Specifications & Style
        add_section("3. Language Specifications & Style")
        ls = style_guide.language_specifications
        st = style_guide.style_tone
        add_kv("Target Dialects", ls.target_dialects)
        add_kv("Language Register", getattr(ls, "language_register", ""))
        add_kv("Voice", ls.voice)
        add_kv("Person Address", ls.person_address)

        add_kv("Overall Tone", st.overall_tone)
        if st.do_instructions:
            doc.add_heading("DOs", level=2)
            for item in st.do_instructions:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(item)
        if st.dont_instructions:
            doc.add_heading("DON'Ts", level=2)
            for item in st.dont_instructions:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(item)
        if st.stylistic_examples:
            doc.add_heading("Stylistic Examples", level=2)
            for ex in st.stylistic_examples:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(ex)

        # 4. Gender & Inclusivity
        add_section("4. Gender & Inclusivity")
        gi = style_guide.gender_inclusivity
        add_kv("General Approach", gi.general_approach)
        add_kv("Pronoun Usage", gi.pronoun_usage)
        add_kv("Inclusive Language Rules", gi.inclusive_language_rules)
        if gi.examples:
            doc.add_heading("Examples", level=2)
            for ex in gi.examples:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(ex)

        # 5. Terminology
        add_section("5. Terminology")
        tr = style_guide.terminology_rules
        if tr.termbase_sources:
            add_kv("Termbase Sources", ", ".join(tr.termbase_sources))
        add_kv("Acronym Handling", tr.acronym_handling)
        add_kv("Term Preferences", tr.term_preferences)
        if tr.forbidden_terms:
            doc.add_heading("Forbidden Terms", level=2)
            for term in tr.forbidden_terms:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(term)

        # 6. Do Not Translate
        add_section("6. Do Not Translate (DNT)")
        dnt = style_guide.dnt_list
        if hasattr(dnt, "brand_and_product_names"):
            add_kv("Brand & Product Names", ", ".join(getattr(dnt, "brand_and_product_names", [])))
        add_kv("Variables / Placeholders / Tags", dnt.variables_placeholders_tags)
        if hasattr(dnt, "special_casing_terms"):
            add_kv("Special Casing Terms", ", ".join(getattr(dnt, "special_casing_terms", [])))

        # 7. Formatting & Locale
        add_section("7. Formatting & Locale")
        fmt = style_guide.formatting_locale
        if hasattr(fmt, "date_format_examples") and getattr(fmt, "date_format_examples", []):
            doc.add_heading("Date Examples", level=2)
            for ex in fmt.date_format_examples:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(ex)

        if hasattr(fmt, "number_format_examples") and getattr(fmt, "number_format_examples", []):
            doc.add_heading("Number & Measurement Examples", level=2)
            for ex in fmt.number_format_examples:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(ex)

        add_kv("Units & Measurements", fmt.units_and_measurements)
        add_kv("Quotation Marks", fmt.quotation_marks)
        add_kv("Bullets & Lists", fmt.bullets_and_lists)

        # 8. Spatial & Visual Guidelines
        add_section("8. Spatial & Visual Guidelines")
        spc = style_guide.spatial_considerations
        vis = style_guide.visual_content
        add_kv("Expansion / Contraction", spc.expansion_contraction)
        add_kv("UI & Layout Limits", spc.ui_and_layout_limits)
        add_kv("Truncation Rules", spc.truncation_rules)
        add_kv("Embedded Text", vis.embedded_text)
        add_kv("Screenshots & UI", vis.screenshots_and_ui)
        add_kv("Culturally Sensitive Imagery", vis.culturally_sensitive_imagery)

        # 9. QA & Resources
        add_section("9. QA & Resources")
        qa = style_guide.quality_assurance
        res = style_guide.reference_resources
        if qa.required_qa_tools:
            add_kv("QA Tools", ", ".join(qa.required_qa_tools))
        add_kv("Thresholds", qa.pass_fail_thresholds)
        if res.standard_glossaries:
            add_kv("Standard Glossaries", ", ".join(res.standard_glossaries))

        # Footer
        doc.add_section()
        fp = doc.add_paragraph(style_guide.footnote)
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fp.runs:
            fp.runs[0].italic = True

        path = os.path.join(self.output_dir, filename)
        doc.save(path)
        return path

    # ---------- helper for plain-text export ----------

    @staticmethod
    def _add_formatted_runs(paragraph, text: str):
        """
        Very simple markdown-style bold handling:
        - Treat **this** as bold.
        Everything else stays normal.
        """
        if "**" not in text:
            paragraph.add_run(text)
            return

        parts = text.split("**")
        for i, part in enumerate(parts):
            if not part:
                continue
            run = paragraph.add_run(part)
            if i % 2 == 1:
                run.bold = True

    # ---------- DOCX export for plain text guide (Claude) ----------

    def export_plaintext_docx(self, guide_text: str, filename: str) -> str:
        """
        Convert the Claude-generated plain text guide into a nicer DOCX:

        - First non-empty line -> Title (centered).
        - Line starting with "PROJECT: " -> centered bold project line.
        - Lines of just '---' -> visual separator line.
        - Lines starting with digits + '.' -> Heading 1 (section titles).
        - Lines starting with '- ', '- [ ]', '- [x]' -> bullet list items.
        - **bold** markers -> bold runs.
        - Everything else -> normal paragraphs.
        """
        doc = Document()

        title_added = False

        for raw_line in guide_text.splitlines():
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            # Empty line -> blank paragraph
            if not stripped:
                doc.add_paragraph()
                continue

            # Separator lines like '---'
            if all(ch == "-" for ch in stripped) and len(stripped) >= 3:
                p = doc.add_paragraph()
                run = p.add_run("─" * 40)
                run.italic = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue

            # First non-empty line -> title
            if not title_added:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                try:
                    p.style = doc.styles["Title"]
                except KeyError:
                    # Fallback: use Heading 0 equivalent
                    p.style = doc.styles["Heading 1"]
                self._add_formatted_runs(p, stripped)
                title_added = True
                continue

            # Project line
            if stripped.upper().startswith("PROJECT: "):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(stripped)
                run.bold = True
                continue

            # Heading detection: "1. SCOPE & PURPOSE"
            first_char = stripped[0]
            if first_char.isdigit():
                prefix, sep, rest = stripped.partition(".")
                if sep and prefix.isdigit():
                    heading_text = rest.strip()
                    # Keep "1. " prefix in the visible text to mirror your sample
                    heading_full = f"{prefix}. {heading_text}" if heading_text else stripped
                    h = doc.add_heading(heading_full, level=1)
                    continue

            # Bullet / checklist lines
            bullet_prefixes = ("- [ ]", "- [x]", "- [X]", "- ")
            if stripped.startswith(bullet_prefixes):
                # Remove the leading marker / checkbox
                cleaned = stripped
                for bp in bullet_prefixes:
                    if cleaned.startswith(bp):
                        cleaned = cleaned[len(bp):].strip()
                        break
                p = doc.add_paragraph(style="List Bullet")
                self._add_formatted_runs(p, cleaned)
                continue

            # Fallback: normal paragraph with inline bold
            p = doc.add_paragraph()
            self._add_formatted_runs(p, stripped)

        path = os.path.join(self.output_dir, filename)
        doc.save(path)
        return path
