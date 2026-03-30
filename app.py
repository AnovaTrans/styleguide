import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from generator import StyleGuideGenerator
from exporter import StyleGuideExporter
from text_utils import DocumentProcessor
from anova_brand_theme import apply_anova_theme, anova_header, anova_footer, anova_sidebar_logo

# Optional: language detection
try:
    from langdetect import detect
except ImportError:
    detect = None


# ---------- Helper functions ----------

SUPPORTED_EXTENSIONS = [
    "docx", "doc", "ppt", "pptx", "pdf",
    "txt", "csv", "xlsx", "xls",
    "json", "xml", "srt",
    "xliff", "xlf", "po",
    "sdlxliff", "mqxliff", "memoqxliff",
]


# Comprehensive language support
LANG_OPTIONS = {
    # EU Languages (27)
    "Bulgarian – bg-BG": "bg-BG",
    "Croatian – hr-HR": "hr-HR",
    "Czech – cs-CZ": "cs-CZ",
    "Danish – da-DK": "da-DK",
    "Dutch – nl-NL": "nl-NL",
    "English (US) – en-US": "en-US",
    "English (UK) – en-GB": "en-GB",
    "Estonian – et-EE": "et-EE",
    "Finnish – fi-FI": "fi-FI",
    "French (France) – fr-FR": "fr-FR",
    "French (Belgium) – fr-BE": "fr-BE",
    "German (Germany) – de-DE": "de-DE",
    "German (Austria) – de-AT": "de-AT",
    "German (Switzerland) – de-CH": "de-CH",
    "Greek – el-GR": "el-GR",
    "Hungarian – hu-HU": "hu-HU",
    "Irish – ga-IE": "ga-IE",
    "Italian – it-IT": "it-IT",
    "Latvian – lv-LV": "lv-LV",
    "Lithuanian – lt-LT": "lt-LT",
    "Luxembourgish – lb-LU": "lb-LU",
    "Maltese – mt-MT": "mt-MT",
    "Polish – pl-PL": "pl-PL",
    "Portuguese (Portugal) – pt-PT": "pt-PT",
    "Portuguese (Brazil) – pt-BR": "pt-BR",
    "Romanian – ro-RO": "ro-RO",
    "Slovak – sk-SK": "sk-SK",
    "Slovenian – sl-SI": "sl-SI",
    "Spanish (Spain) – es-ES": "es-ES",
    "Spanish (Mexico) – es-MX": "es-MX",
    "Spanish (Argentina) – es-AR": "es-AR",
    "Swedish – sv-SE": "sv-SE",
    
    # Non-EU European Languages
    "Albanian – sq-AL": "sq-AL",
    "Belarusian – be-BY": "be-BY",
    "Bosnian – bs-BA": "bs-BA",
    "Icelandic – is-IS": "is-IS",
    "Macedonian – mk-MK": "mk-MK",
    "Norwegian – no-NO": "no-NO",
    "Russian – ru-RU": "ru-RU",
    "Serbian – sr-RS": "sr-RS",
    "Ukrainian – uk-UA": "uk-UA",
    
    # Additional Major Languages
    "Turkish – tr-TR": "tr-TR",
    "Arabic (Modern Standard) – ar-SA": "ar-SA",
    "Arabic (Egyptian) – ar-EG": "ar-EG",
    "Chinese (Simplified) – zh-CN": "zh-CN",
    "Chinese (Traditional) – zh-TW": "zh-TW",
    "Japanese – ja-JP": "ja-JP",
    "Korean – ko-KR": "ko-KR",
    "Thai – th-TH": "th-TH",
    "Vietnamese – vi-VN": "vi-VN",
    "Indonesian – id-ID": "id-ID",
    "Hindi – hi-IN": "hi-IN",
    "Hebrew – he-IL": "he-IL",
    "Afrikaans – af-ZA": "af-ZA",
}


def detect_source_language_from_files(temp_paths):
    if not detect:
        return "unknown"

    # Concatenate small chunks from all files for detection
    collected = []
    for p in temp_paths:
        text = DocumentProcessor.read_file(p)
        if text:
            collected.append(text[:4000])  # avoid huge blobs

    if not collected:
        return "unknown"

    try:
        lang_code = detect("\n\n".join(collected))
    except Exception:
        return "unknown"

    # Extended language detection mapping
    mapping = {
        "bg": "bg-BG",
        "hr": "hr-HR",
        "cs": "cs-CZ",
        "da": "da-DK",
        "nl": "nl-NL",
        "de": "de-DE",
        "en": "en-US",
        "et": "et-EE",
        "fi": "fi-FI",
        "fr": "fr-FR",
        "el": "el-GR",
        "hu": "hu-HU",
        "ga": "ga-IE",
        "it": "it-IT",
        "lv": "lv-LV",
        "lt": "lt-LT",
        "lb": "lb-LU",
        "mt": "mt-MT",
        "pl": "pl-PL",
        "pt": "pt-PT",
        "pt-br": "pt-BR",
        "ro": "ro-RO",
        "sk": "sk-SK",
        "sl": "sl-SI",
        "es": "es-ES",
        "sv": "sv-SE",
        "sq": "sq-AL",
        "be": "be-BY",
        "bs": "bs-BA",
        "is": "is-IS",
        "mk": "mk-MK",
        "no": "no-NO",
        "ru": "ru-RU",
        "sr": "sr-RS",
        "uk": "uk-UA",
        "tr": "tr-TR",
        "ar": "ar-SA",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "th": "th-TH",
        "vi": "vi-VN",
        "id": "id-ID",
        "hi": "hi-IN",
        "he": "he-IL",
        "af": "af-ZA",
    }
    return mapping.get(lang_code.lower(), lang_code)


def get_anthropic_key_from_env_or_ui():
    load_dotenv()
    env_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    st.sidebar.subheader("API Configuration")
    manual_key = st.sidebar.text_input(
        "Anthropic API Key (leave empty to use environment variable)",
        type="password",
        value="",
    ).strip()

    if manual_key:
        return manual_key
    return env_key


# ---------- Streamlit UI ----------

st.set_page_config(page_title="Anova Style Guide Creator", page_icon="📝", layout="wide")

apply_anova_theme()

anova_header("Style Guide Creator", "AI-powered translation style guide generation")

st.markdown(
    """
**Supported formats:**  
`*.docx, *.doc, *.ppt, *.pptx, *.pdf (max 100 pages), *.txt, *.csv, *.xlsx, *.xls, *.json, *.xml, *.srt, *.xliff, *.xlf, *.po, *.sdlxliff, *.mqxliff, *.memoqxliff`
"""
)

# File upload
uploaded_files = st.file_uploader(
    "Upload up to 10 files (max 30 MB total)",
    type=SUPPORTED_EXTENSIONS,
    accept_multiple_files=True,
)

col1, col2 = st.columns(2)

with col1:
    source_lang_mode = st.selectbox(
        "Source Language",
        ["Auto-detect"] + list(LANG_OPTIONS.keys()),
    )

with col2:
    target_labels = st.multiselect(
        "Target Languages (optional – leave empty for generic style guide)",
        list(LANG_OPTIONS.keys()),
    )

# Sidebar content
anova_sidebar_logo()

# Advanced options (model)
st.sidebar.subheader("Model Settings")
model_choice = st.sidebar.selectbox(
    "Claude Model",
    [
        "claude-sonnet-4-5-20250929  (Sonnet 4.5 – default)",
        "claude-opus-4-1-20250805    (Opus 4.1)",
        "claude-haiku-4-5-20251001   (Haiku 4.5)",
        "Custom model ID",
    ],
)

if "Sonnet 4.5" in model_choice:
    selected_model = "claude-sonnet-4-5-20250929"
elif "Opus 4.1" in model_choice:
    selected_model = "claude-opus-4-1-20250805"
elif "Haiku 4.5" in model_choice:
    selected_model = "claude-haiku-4-5-20251001"
else:
    selected_model = st.sidebar.text_input("Custom Claude model ID", "").strip()

st.sidebar.markdown("---")
api_key = get_anthropic_key_from_env_or_ui()
if not api_key:
    st.sidebar.warning("No ANTHROPIC_API_KEY found. Enter it above or set it in your environment.")

generate_btn = st.button("Generate Style Guide", type="primary")


# ---------- Main action ----------

if generate_btn:
    if not uploaded_files:
        st.error("Please upload at least one file.")
    elif not api_key:
        st.error("Anthropic API key is missing.")
    elif not selected_model:
        st.error("Please select or enter a Claude model.")
    else:
        with st.spinner("Processing files and generating style guide…"):
            # Save uploaded files to temp directory
            temp_dir = tempfile.mkdtemp(prefix="styleguide_")
            temp_paths = []
            for uf in uploaded_files:
                temp_path = os.path.join(temp_dir, uf.name)
                with open(temp_path, "wb") as f:
                    f.write(uf.getbuffer())
                temp_paths.append(temp_path)

            # Project name from first file
            first_name = os.path.basename(temp_paths[0])
            project_name = os.path.splitext(first_name)[0]

            # Determine source language
            if source_lang_mode == "Auto-detect":
                detected = detect_source_language_from_files(temp_paths)
                if detected == "unknown":
                    source_lang = "unknown"
                    st.warning(
                        "Could not auto-detect source language reliably. "
                        "The guide will be more generic."
                    )
                else:
                    source_lang = detected
            else:
                source_lang = LANG_OPTIONS[source_lang_mode]

            # Target languages
            target_langs = [LANG_OPTIONS[label] for label in target_labels]

            try:
                generator = StyleGuideGenerator(
                    api_key=api_key,
                    provider="anthropic",
                    model=selected_model,
                )

                exporter = StyleGuideExporter(output_dir=temp_dir)

                guide_text = generator.create_guide_text(
                    file_paths=temp_paths,
                    source_lang=source_lang,
                    target_langs=target_langs,
                    project_name=project_name,
                )

                output_filename = f"{project_name}_style_guide_claude.docx"
                output_path = exporter.export_plaintext_docx(
                    guide_text,
                    output_filename,
                )

                with open(output_path, "rb") as f:
                    data = f.read()

                st.success("Style guide successfully generated.")
                st.download_button(
                    "⬇️ Download Style Guide",
                    data=data,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

            except Exception as e:
                st.error(f"Error during generation: {e}")

anova_footer()
