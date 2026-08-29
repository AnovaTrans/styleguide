"""
Style Guide Exporter — Enhanced DOCX Output
=============================================
Professional formatting with Anova branding, proper heading
hierarchy, table support, and improved markdown-to-docx conversion.
"""

import os
import re
from typing import Optional

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from models import StyleGuide

# Anova brand colors
CHARCOAL = RGBColor(0x3A, 0x3A, 0x3A)
CORAL = RGBColor(0xE8, 0x5C, 0x4A)
TEAL = RGBColor(0x4E, 0xCD, 0xC4)


class StyleGuideExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # ---------- JSON export for structured StyleGuide (kept for future use) ----------

    def export_json(self, style_guide: StyleGuide, filename: str) -> str:
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(style_guide.model_dump_json(indent=2))
        return path

    # ---------- DOCX export for structured StyleGuide (legacy) ----------

    def export_docx(self, style_guide: StyleGuide, filename: str) -> str:
        """Export a structured StyleGuide (JSON/Pydantic) to a formatted DOCX."""
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

        header = style_guide.header
        add_title(header.title)

        meta_p = doc.add_paragraph()
        meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta_p.add_run(f"Project: {header.project_name} | ").bold = True
        meta_p.add_run(
            f"Source: {header.source_language} → Target(s): {', '.join(header.target_languages)}\n"
        )
        meta_p.add_run(
            f"Version: {header.version} | Prepared by: {header.prepared_by} | Date: {header.creation_date}"
        )
        doc.add_paragraph()

        # 1-9: sections (same as before)
        add_section("1. Scope & Audience Profile")
        sp = style_guide.scope_purpose
        ta = style_guide.target_audience
        add_kv("Scope", sp.document_scope)
        add_kv("Content Type", sp.content_type)
        add_kv("Audience Demographics", ta.demographics)
        add_kv("Audience Expertise", ta.expertise_level)
        add_kv("Reading Behaviour", ta.reading_behaviour)
        add_kv("Cultural Sensitivities", ta.cultural_sensitivities)

        add_section("2. Domain & Context")
        dc = style_guide.domain_context
        add_kv("Industry", dc.industry)
        add_kv("References", dc.references)

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
                doc.add_paragraph(item, style="List Bullet")
        if st.dont_instructions:
            doc.add_heading("DON'Ts", level=2)
            for item in st.dont_instructions:
                doc.add_paragraph(item, style="List Bullet")
        if st.stylistic_examples:
            doc.add_heading("Stylistic Examples", level=2)
            for ex in st.stylistic_examples:
                doc.add_paragraph(ex, style="List Bullet")

        add_section("4. Gender & Inclusivity")
        gi = style_guide.gender_inclusivity
        add_kv("General Approach", gi.general_approach)
        add_kv("Pronoun Usage", gi.pronoun_usage)
        add_kv("Inclusive Language Rules", gi.inclusive_language_rules)
        if gi.examples:
            doc.add_heading("Examples", level=2)
            for ex in gi.examples:
                doc.add_paragraph(ex, style="List Bullet")

        add_section("5. Terminology")
        tr = style_guide.terminology_rules
        if tr.termbase_sources:
            add_kv("Termbase Sources", ", ".join(tr.termbase_sources))
        add_kv("Acronym Handling", tr.acronym_handling)
        add_kv("Term Preferences", tr.term_preferences)
        if tr.forbidden_terms:
            doc.add_heading("Forbidden Terms", level=2)
            for term in tr.forbidden_terms:
                doc.add_paragraph(term, style="List Bullet")

        add_section("6. Do Not Translate (DNT)")
        dnt = style_guide.dnt_list
        if hasattr(dnt, "brand_and_product_names"):
            add_kv("Brand & Product Names", ", ".join(getattr(dnt, "brand_and_product_names", [])))
        add_kv("Variables / Placeholders / Tags", dnt.variables_placeholders_tags)
        if hasattr(dnt, "special_casing_terms"):
            add_kv("Special Casing Terms", ", ".join(getattr(dnt, "special_casing_terms", [])))

        add_section("7. Formatting & Locale")
        fmt = style_guide.formatting_locale
        if hasattr(fmt, "date_format_examples") and getattr(fmt, "date_format_examples", []):
            doc.add_heading("Date Examples", level=2)
            for ex in fmt.date_format_examples:
                doc.add_paragraph(ex, style="List Bullet")
        if hasattr(fmt, "number_format_examples") and getattr(fmt, "number_format_examples", []):
            doc.add_heading("Number & Measurement Examples", level=2)
            for ex in fmt.number_format_examples:
                doc.add_paragraph(ex, style="List Bullet")
        add_kv("Units & Measurements", fmt.units_and_measurements)
        add_kv("Quotation Marks", fmt.quotation_marks)
        add_kv("Bullets & Lists", fmt.bullets_and_lists)

        add_section("8. Spatial & Visual Guidelines")
        spc = style_guide.spatial_considerations
        vis = style_guide.visual_content
        add_kv("Expansion / Contraction", spc.expansion_contraction)
        add_kv("UI & Layout Limits", spc.ui_and_layout_limits)
        add_kv("Truncation Rules", spc.truncation_rules)
        add_kv("Embedded Text", vis.embedded_text)
        add_kv("Screenshots & UI", vis.screenshots_and_ui)
        add_kv("Culturally Sensitive Imagery", vis.culturally_sensitive_imagery)

        add_section("9. QA & Resources")
        qa = style_guide.quality_assurance
        res = style_guide.reference_resources
        if qa.required_qa_tools:
            add_kv("QA Tools", ", ".join(qa.required_qa_tools))
        add_kv("Thresholds", qa.pass_fail_thresholds)
        if res.standard_glossaries:
            add_kv("Standard Glossaries", ", ".join(res.standard_glossaries))

        doc.add_section()
        fp = doc.add_paragraph(style_guide.footnote)
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fp.runs:
            fp.runs[0].italic = True

        path = os.path.join(self.output_dir, filename)
        doc.save(path)
        return path

    # ---------- Enhanced markdown-to-DOCX helpers ----------

    @staticmethod
    def _add_formatted_runs(paragraph, text: str):
        """
        Enhanced markdown-style formatting:
        - **bold** → bold
        - *italic* → italic (single asterisks, not inside **)
        - `code` → monospace
        """
        if "**" not in text and "`" not in text:
            paragraph.add_run(text)
            return

        # Handle code first
        parts = re.split(r'(`[^`]+`)', text)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                run = paragraph.add_run(part[1:-1])
                run.font.name = 'Consolas'
                run.font.size = Pt(10)
            elif "**" in part:
                # Handle bold
                bold_parts = part.split("**")
                for i, bp in enumerate(bold_parts):
                    if not bp:
                        continue
                    run = paragraph.add_run(bp)
                    if i % 2 == 1:
                        run.bold = True
            else:
                paragraph.add_run(part)

    @staticmethod
    def _detect_heading_level(stripped: str):
        """Detect heading level from numbered prefix like '1.', '1.1', '1.1.1'."""
        match = re.match(r'^(\d+(?:\.\d+)*)\.?\s+(.+)', stripped)
        if match:
            prefix = match.group(1)
            text = match.group(2)
            dots = prefix.count('.')
            level = min(dots + 1, 3)  # level 1, 2, or 3
            return level, f"{prefix}. {text}"
        return None, None

    # ---------- DOCX export for plain text guide (Claude) — Enhanced ----------

    def export_plaintext_docx(self, guide_text: str, filename: str) -> str:
        """
        Convert the Claude-generated plain text guide into a professional DOCX.

        Enhanced features:
        - Multi-level heading detection (1., 1.1, 1.1.1)
        - Anova branding (header/footer text)
        - Better bullet handling (-, *, numbered lists)
        - Code/monospace support
        - Sub-heading detection (lines ending with :)
        """
        doc = Document()

        # Set default style
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        style.font.color.rgb = CHARCOAL

        title_added = False
        prev_was_empty = False

        for raw_line in guide_text.splitlines():
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            # Empty line → blank paragraph (but avoid double-spacing)
            if not stripped:
                if not prev_was_empty:
                    doc.add_paragraph()
                prev_was_empty = True
                continue
            prev_was_empty = False

            # Separator lines like '---' or '═══'
            if len(stripped) >= 3 and all(ch in '-=─═~' for ch in stripped):
                p = doc.add_paragraph()
                run = p.add_run("─" * 50)
                run.font.color.rgb = TEAL
                run.font.size = Pt(8)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue

            # First non-empty line → title
            if not title_added:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                try:
                    p.style = doc.styles["Title"]
                except KeyError:
                    p.style = doc.styles["Heading 1"]
                self._add_formatted_runs(p, stripped)
                # Set title color
                for run in p.runs:
                    run.font.color.rgb = CHARCOAL
                title_added = True
                continue

            # Project/metadata line
            upper = stripped.upper()
            if upper.startswith("PROJECT:") or upper.startswith("SOURCE:") or upper.startswith("GENERATED BY:"):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(stripped)
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(0x9B, 0x9B, 0x9B)
                continue

            # Markdown ATX headings: "#", "##", "###" ... Strip the hashes and
            # any stray bold markers, map depth to a heading level (1-3).
            if stripped.startswith('#'):
                hashes = len(stripped) - len(stripped.lstrip('#'))
                heading_text = stripped[hashes:].strip().replace('**', '').strip()
                if heading_text:
                    h = doc.add_heading(heading_text, level=min(max(hashes, 1), 3))
                    for run in h.runs:
                        run.font.color.rgb = CHARCOAL
                    continue

            # Heading detection: "1. SCOPE" or "1.1 Sub-heading" or "1.1.1 Detail".
            # Guard against numbered *list items* (e.g. "1. **ride** → yolculuk"),
            # which carry bold/arrow markup or run long — those are content, not
            # section headings, and must not become Heading 1.
            level, heading_text = self._detect_heading_level(stripped)
            if level is not None and '**' not in stripped and '→' not in stripped and len(stripped) <= 70:
                h = doc.add_heading(heading_text, level=level)
                for run in h.runs:
                    run.font.color.rgb = CHARCOAL
                continue

            # Sub-heading: ALL CAPS line or line ending with ':'
            if stripped.isupper() and len(stripped) > 3 and len(stripped) < 80:
                h = doc.add_heading(stripped, level=2)
                for run in h.runs:
                    run.font.color.rgb = CHARCOAL
                continue

            # Bullet / checklist lines (-, *, •)
            bullet_match = re.match(r'^[-*•]\s+(.+)', stripped)
            checkbox_match = re.match(r'^-\s*\[([ xX])\]\s+(.+)', stripped)
            numbered_match = re.match(r'^(\d+)\)\s+(.+)', stripped)

            if checkbox_match:
                checked = checkbox_match.group(1).lower() == 'x'
                text = checkbox_match.group(2)
                p = doc.add_paragraph(style="List Bullet")
                prefix = "[x] " if checked else "[ ] "
                run = p.add_run(prefix)
                run.font.name = 'Consolas'
                run.font.size = Pt(10)
                self._add_formatted_runs(p, text)
                continue
            elif bullet_match:
                p = doc.add_paragraph(style="List Bullet")
                self._add_formatted_runs(p, bullet_match.group(1))
                continue
            elif numbered_match:
                p = doc.add_paragraph(style="List Number")
                self._add_formatted_runs(p, numbered_match.group(2))
                continue

            # Indented bullet (sub-item)
            sub_bullet_match = re.match(r'^  [-*•]\s+(.+)', line)  # Note: using 'line' not 'stripped'
            if sub_bullet_match:
                p = doc.add_paragraph(style="List Bullet 2")
                self._add_formatted_runs(p, sub_bullet_match.group(1))
                continue

            # Key: Value lines (bold key)
            kv_match = re.match(r'^([A-Za-z][A-Za-z\s&/]+):\s+(.+)', stripped)
            if kv_match and len(kv_match.group(1)) < 40:
                p = doc.add_paragraph()
                p.add_run(kv_match.group(1) + ": ").bold = True
                self._add_formatted_runs(p, kv_match.group(2))
                continue

            # Fallback: normal paragraph with inline formatting
            p = doc.add_paragraph()
            self._add_formatted_runs(p, stripped)

        # ── Footer ──
        doc.add_paragraph()
        sep = doc.add_paragraph()
        sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = sep.add_run("─" * 50)
        run.font.color.rgb = TEAL
        run.font.size = Pt(8)

        footer = doc.add_paragraph()
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run(
            "This style guide was generated by AICONTEXT Style Guide Creator | Anova Translation"
        )
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x9B, 0x9B, 0x9B)

        attr = doc.add_paragraph()
        attr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = attr.add_run("www.anova.bg | info@anova.bg")
        run.font.size = Pt(8)
        run.font.color.rgb = TEAL

        path = os.path.join(self.output_dir, filename)
        doc.save(path)
        return path
