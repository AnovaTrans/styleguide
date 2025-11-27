from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import date


# =========================
# Header & Project Info
# =========================

class Header(BaseModel):
    title: str = Field(
        default="Translation / Localization Style Guide",
        description="Main title of the style guide."
    )
    project_name: str = Field(
        ...,
        description="Human-readable project name."
    )
    source_language: str = Field(
        ...,
        description="Source language (e.g. de-DE)."
    )
    target_languages: List[str] = Field(
        ...,
        description="List of target language codes or labels."
    )
    version: str = Field(
        default="1.0",
        description="Version of the style guide."
    )
    prepared_by: str = Field(
        default="AI Style Guide Generator",
        description="Who prepared the guide."
    )
    creation_date: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Generation date in ISO format."
    )


# =========================
# Scope & Audience
# =========================

class ScopeAndPurpose(BaseModel):
    document_scope: str = Field(..., description="High-level scope of the guide.")
    content_type: str = Field(..., description="Content type (marketing, technical, etc.).")


class TargetAudienceProfile(BaseModel):
    demographics: str = Field(..., description="Description of target audience.")
    expertise_level: str = Field(..., description="Knowledge level of audience.")
    reading_behaviour: str = Field(..., description="Reading patterns (skimming, deep reading).")
    cultural_sensitivities: str = Field(..., description="Cultural or regional sensitivities.")


# =========================
# Domain & Language
# =========================

class DomainContext(BaseModel):
    industry: str = Field(..., description="Primary industry or domain.")
    references: str = Field(..., description="Relevant standards and frameworks.")


class LanguageSpecifications(BaseModel):
    target_dialects: str = Field(..., description="Target language variants (e.g. en-US).")
    language_register: str = Field(..., description="Formality level / linguistic register.")
    voice: str = Field(..., description="Active vs passive and tone style.")
    person_address: str = Field(..., description="Form of address, pronouns, etc.")


# =========================
# Style & Tone
# =========================

class StyleAndTone(BaseModel):
    overall_tone: str = Field(..., description="Overall tone and style.")
    do_instructions: List[str] = Field(default_factory=list, description="What to do.")
    dont_instructions: List[str] = Field(default_factory=list, description="What not to do.")
    stylistic_examples: List[str] = Field(default_factory=list, description="Style examples.")


# =========================
# Gender & Inclusivity
# =========================

class GenderAndInclusivity(BaseModel):
    general_approach: str = Field(..., description="Inclusivity strategy.")
    pronoun_usage: str = Field(..., description="Pronoun rules.")
    inclusive_language_rules: str = Field(..., description="Inclusive language rules.")
    examples: List[str] = Field(default_factory=list, description="Practical examples.")


# =========================
# Terminology
# =========================

class TerminologyRules(BaseModel):
    termbase_sources: List[str] = Field(default_factory=list, description="Glossary sources.")
    acronym_handling: str = Field(..., description="Handling of acronyms.")
    term_preferences: str = Field(..., description="Preferred term rules.")
    forbidden_terms: List[str] = Field(default_factory=list, description="Disallowed terms.")


# =========================
# Do Not Translate
# =========================

class DoNotTranslate(BaseModel):
    brand_and_product_names: List[str] = Field(
        default_factory=list,
        description="Names that must not be translated."
    )

    variables_placeholders_tags: str = Field(
        ...,
        description="Rules for placeholders, variables and tags."
    )

    special_casing_terms: List[str] = Field(
        default_factory=list,
        description="Terms with special casing that must be preserved."
    )

    named_entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description=(
            "Grouped named entities from the source. "
            "Keys: companies, products, people, places, institutions."
        )
    )


# =========================
# Formatting & Locale
# =========================

class FormattingAndLocale(BaseModel):
    date_format_examples: List[str] = Field(
        default_factory=list,
        description="Real date examples and conversions."
    )

    number_format_examples: List[str] = Field(
        default_factory=list,
        description="Real numeric/measurement examples and conversions."
    )

    units_and_measurements: str = Field(
        ...,
        description="Unit conversion and measurement rules."
    )

    quotation_marks: str = Field(
        ...,
        description="Quotation mark usage rules."
    )

    bullets_and_lists: str = Field(
        ...,
        description="Bullet and list formatting rules."
    )


# =========================
# Spatial & Visual
# =========================

class SpatialConsiderations(BaseModel):
    expansion_contraction: str = Field(..., description="Expansion/contraction expectations.")
    ui_and_layout_limits: str = Field(..., description="UI and layout constraints.")
    truncation_rules: str = Field(..., description="Truncation behavior.")


class VisualContentGuidelines(BaseModel):
    embedded_text: str = Field(..., description="Text inside images.")
    screenshots_and_ui: str = Field(..., description="UI localization rules.")
    culturally_sensitive_imagery: str = Field(..., description="Handling of sensitive visuals.")


# =========================
# QA & Resources
# =========================

class QualityAssurance(BaseModel):
    required_qa_tools: List[str] = Field(default_factory=list, description="QA tools.")
    pass_fail_thresholds: str = Field(..., description="Quality thresholds.")
    escalation_rules_to_pm: str = Field(..., description="Escalation rules.")


class ReferenceResources(BaseModel):
    standard_glossaries: List[str] = Field(default_factory=list, description="External references.")
    client_assets: List[str] = Field(default_factory=list, description="Client assets.")
    online_dictionaries: List[str] = Field(default_factory=list, description="Online dictionaries.")


# =========================
# Root Model
# =========================

class StyleGuide(BaseModel):
    header: Header
    scope_purpose: ScopeAndPurpose
    target_audience: TargetAudienceProfile
    domain_context: DomainContext
    language_specifications: LanguageSpecifications
    style_tone: StyleAndTone
    gender_inclusivity: GenderAndInclusivity
    terminology_rules: TerminologyRules
    dnt_list: DoNotTranslate
    formatting_locale: FormattingAndLocale
    spatial_considerations: SpatialConsiderations
    visual_content: VisualContentGuidelines
    quality_assurance: QualityAssurance
    reference_resources: ReferenceResources

    footnote: str = Field(
        default="This style guide is auto-generated by AI. Validate with a subject matter expert before use.",
        description="AI disclosure note."
    )
