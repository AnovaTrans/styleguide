import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from generator import StyleGuideGenerator
from exporter import StyleGuideExporter
from text_utils import DocumentProcessor

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


LANG_OPTIONS = {
    "German (Germany) – de-DE": "de-DE",
    "English (US) – en-US": "en-US",
    "English (UK) – en-GB": "en-GB",
    "French (France) – fr-FR": "fr-FR",
    "Spanish (Spain) – es-ES": "es-ES",
    "Italian (Italy) – it-IT": "it-IT",
    "Turkish – tr-TR": "tr-TR",
    "Portuguese (Portugal) – pt-PT": "pt-PT",
    "Portuguese (Brazil) – pt-BR": "pt-BR",
    "Chinese (Simplified) – zh-CN": "zh-CN",
    "Chinese (Traditional) – zh-TW": "zh-TW",
    "Japanese – ja-JP": "ja-JP",
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

    mapping = {
        "de": "de-DE",
        "en": "en-US",
        "fr": "fr-FR",
        "tr": "tr-TR",
        "es": "es-ES",
        "it": "it-IT",
        "pt": "pt-PT",
        "pt-br": "pt-BR",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "ja": "ja-JP",
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

st.set_page_config(page_title="Style Guide Generator", layout="wide")

st.title("Style Guide Generator")
st.caption(
    "Complete confidentiality guaranteed – files are processed locally with your API key."
)

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
