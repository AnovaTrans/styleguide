import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from generator import StyleGuideGenerator
from exporter import StyleGuideExporter
from text_utils import DocumentProcessor
from anova_brand_theme import apply_anova_theme, anova_header, anova_footer, anova_sidebar_logo
import model_utils


@st.cache_data(show_spinner=False)
def _cached_model_ids(api_key: str):
    """Live current-generation model ids, cached per key so the Models API
    isn't hit on every rerun."""
    return model_utils.list_model_ids(api_key)

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

# API key first, so the model list can be fetched live from the account.
api_key = get_anthropic_key_from_env_or_ui()

# Advanced options (model) — list fetched live from the account (current-
# generation only), with a manual override. Falls back to a current-only
# static list when the Models API can't be reached.
st.sidebar.subheader("Model Settings")
live_ids = _cached_model_ids(api_key)
base_ids = live_ids or model_utils.FALLBACK_MODELS
model_options = list(base_ids) + ["Custom model ID"]
default_id = model_utils.default_model(base_ids)
default_index = model_options.index(default_id) if default_id in model_options else 0
model_choice = st.sidebar.selectbox(
    "Claude Model",
    model_options,
    index=default_index,
    format_func=lambda mid: mid if mid == "Custom model ID" else model_utils.display_name(mid),
)
if model_choice == "Custom model ID":
    selected_model = st.sidebar.text_input("Custom Claude model ID", "").strip()
else:
    selected_model = model_choice
if api_key and not live_ids:
    st.sidebar.caption("⚠️ Couldn't fetch the live model list — showing current-generation defaults.")

# Generation mode
st.sidebar.subheader("Generation Mode")
generation_mode = st.sidebar.selectbox(
    "Quality vs Speed",
    [
        "Multi-pass (Recommended – highest quality)",
        "Single-pass (Faster, lower cost)",
    ],
)
use_multi_pass = "Multi-pass" in generation_mode

# Detail level selection
st.sidebar.subheader("Detail Level")
detail_level_choice = st.sidebar.radio(
    "Style guide detail level",
    [
        "Comprehensive (~5000 words)",
        "Standard (~3000-3500 words)",
        "Basic (~1000-1500 words)",
    ],
    index=0,
    help="All levels cover the same 9 sections. Higher levels include more examples and deeper analysis.",
)

if "Comprehensive" in detail_level_choice:
    selected_detail_level = "comprehensive"
elif "Standard" in detail_level_choice:
    selected_detail_level = "standard"
else:
    selected_detail_level = "basic"

st.sidebar.markdown("---")
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
        # Progress bar UI elements
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(percent, message):
            """Callback for real-time progress updates."""
            percent = max(0, min(100, percent))
            progress_bar.progress(percent / 100.0)
            status_text.text(f"⏳ {message} ({percent}%)")

        update_progress(1, "Preparing files...")

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
        update_progress(3, "Detecting source language...")
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
                multi_pass=use_multi_pass,
                detail_level=selected_detail_level,
                progress_callback=update_progress,
            )

            update_progress(95, "Exporting to DOCX...")

            output_filename = f"{project_name}_style_guide_claude.docx"
            output_path = exporter.export_plaintext_docx(
                guide_text,
                output_filename,
            )

            with open(output_path, "rb") as f:
                data = f.read()

            update_progress(100, "Complete!")
            progress_bar.progress(1.0)
            status_text.empty()

            # Store the result (bytes + metadata) so the download button and
            # success message survive the rerun a download click triggers — a
            # button rendered inside this `if generate_btn` block would vanish.
            st.session_state.sg_result = {
                "data": data,
                "filename": output_filename,
                "word_count": len(guide_text.split()),
                "detail_level": selected_detail_level,
            }

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Error during generation: {e}")

# Persistent result — rendered from session_state so it (and the download
# button) stay after a download triggers a rerun.
sg_result = st.session_state.get("sg_result")
if sg_result:
    st.success(
        f"Style guide generated successfully! "
        f"({sg_result['word_count']:,} words, {sg_result['detail_level']} level)"
    )
    st.download_button(
        "⬇️ Download Style Guide",
        data=sg_result["data"],
        file_name=sg_result["filename"],
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

anova_footer()
