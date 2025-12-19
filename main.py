import os
import sys
from dotenv import load_dotenv

from generator import StyleGuideGenerator
from exporter import StyleGuideExporter
from text_utils import DocumentProcessor

# Try to import langdetect for automatic source language detection
try:
    from langdetect import detect
except ImportError:
    detect = None


def choose_claude_model() -> str:
    print("\nSelect Claude Model Version:")
    print("1. Sonnet 4.5 (Best Balance) [Default]")
    print("2. Opus 4.1 (Complex Reasoning/Coding)")
    print("3. Haiku 4.5 (Fast/Cost-Optimized)")
    print("4. Enter Custom Model ID")
    choice = input("Enter your choice (1-4): ").strip()

    if choice == "2":
        return "claude-opus-4-1-20250805"
    elif choice == "3":
        return "claude-haiku-4-5-20251001"
    elif choice == "4":
        return input("Enter custom Claude model ID: ").strip()
    else:
        print("Selected Default: claude-sonnet-4-5-20250929")
        return "claude-sonnet-4-5-20250929"


def detect_source_language(file_path: str) -> str:
    text = DocumentProcessor.read_file(file_path)

    if not text or not text.strip():
        return "unknown"

    if detect is None:
        return "unknown"

    try:
        lang_code = detect(text)
    except Exception:
        return "unknown"

    # Extended language detection mapping
    mapping = {
        # EU Languages
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
        
        # Non-EU European Languages
        "sq": "sq-AL",
        "be": "be-BY",
        "bs": "bs-BA",
        "is": "is-IS",
        "mk": "mk-MK",
        "no": "no-NO",
        "ru": "ru-RU",
        "sr": "sr-RS",
        "uk": "uk-UA",
        
        # Additional Major Languages
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


def main():
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment.")
        sys.exit(1)

    model = choose_claude_model()

    file_path = input("\nEnter the full filename/path to process: ").strip()
    if not os.path.exists(file_path):
        print("ERROR: File not found.")
        sys.exit(1)

    # Project name from filename (option 1)
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    project_name = base_filename

    # Detect source language
    print("\nDetecting source language...")
    detected_source = detect_source_language(file_path)

    if detected_source == "unknown":
        source_lang = input("Enter source language code (e.g. de-DE, en-US): ").strip() or "unknown"
    else:
        print(f"Detected source language: {detected_source}")
        override = input("Press ENTER to accept, or type a different code: ").strip()
        source_lang = override if override else detected_source

    # Ask for target languages
    print("\nEnter target language codes (comma-separated).")
    print("Leave empty for GENERIC multi-target style guide.")
    target_input = input("Target languages: ").strip()

    if target_input:
        target_langs = [t.strip() for t in target_input.split(",") if t.strip()]
    else:
        target_langs = []  # generic mode

    print("\nInitializing Claude client...")
    print(f"Using model: {model}")
    print(f"Project name: {project_name}")
    print(f"Source language: {source_lang}")
    print(f"Target languages: {target_langs if target_langs else 'GENERIC'}")

    try:
        generator = StyleGuideGenerator(
            api_key=api_key,
            provider="anthropic",
            model=model
        )

        exporter = StyleGuideExporter("output")

        guide_text = generator.create_guide_text(
            file_paths=[file_path],
            source_lang=source_lang,
            target_langs=target_langs,
            project_name=project_name,
        )

        output_file = exporter.export_plaintext_docx(
            guide_text,
            f"{project_name}_style_guide_claude.docx"
        )

        print("\n✅ Style guide successfully created:")
        print(output_file)

    except Exception as e:
        print("\nERROR during generation:")
        print(str(e))


if __name__ == "__main__":
    main()
