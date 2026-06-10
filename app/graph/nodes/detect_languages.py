from typing import List

from app.core.models import FileChange, FileChangeType, Language

LANGUAGE_MAP = {
    ".java": Language.JAVA,
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".c": Language.CPP,
    ".h": Language.CPP,
    ".hpp": Language.CPP,
    ".hxx": Language.CPP,
    ".ada": Language.ADA,
    ".adb": Language.ADA,
    ".ads": Language.ADA,
    ".md": Language.MARKDOWN,
    ".mdx": Language.MARKDOWN,
    ".rst": Language.MARKDOWN,
}

TEST_PATTERNS = ["test", "spec", "_test", "_spec", "tests/", "test_", "spec_"]


def detect_language(file_path: str) -> Language:
    """Detect language from file extension."""
    for ext, lang in LANGUAGE_MAP.items():
        if file_path.endswith(ext):
            return lang
    return Language.UNKNOWN


def is_test_file(file_path: str) -> bool:
    """Check if file is a test file based on path patterns."""
    path_lower = file_path.lower()
    for pattern in TEST_PATTERNS:
        if pattern in path_lower:
            return True
    return False


def detect_languages_from_files(file_paths: List[str]) -> List[FileChange]:
    """Detect languages for a list of file paths and return FileChange objects."""
    files = []
    for path in file_paths:
        lang = detect_language(path)
        is_test = is_test_file(path)
        files.append(FileChange(
            path=path,
            language=lang,
            change_type=FileChangeType.MODIFIED,
            is_test=is_test,
        ))
    return files


def get_unique_languages(files: List[FileChange]) -> List[Language]:
    """Extract unique languages from a list of FileChange objects."""
    seen = set()
    languages = []
    for file in files:
        if file.language not in seen and file.language != Language.UNKNOWN:
            seen.add(file.language)
            languages.append(file.language)
    return languages