from app.core.models import FileChange, Language
from app.graph.nodes.detect_languages import (
    detect_language,
    detect_languages_from_files,
    get_unique_languages,
    is_test_file,
)


class TestDetectLanguage:
    def test_java_files(self):
        assert detect_language("src/main/java/UserService.java") == Language.JAVA

    def test_python_files(self):
        assert detect_language("scripts/process_data.py") == Language.PYTHON
        assert detect_language("app/main.pyw") == Language.PYTHON

    def test_cpp_files(self):
        assert detect_language("src/main.cpp") == Language.CPP
        assert detect_language("src/main.cc") == Language.CPP
        assert detect_language("src/main.cxx") == Language.CPP
        assert detect_language("src/main.c") == Language.CPP
        assert detect_language("include/header.h") == Language.CPP
        assert detect_language("include/header.hpp") == Language.CPP

    def test_ada_files(self):
        assert detect_language("src/main.ada") == Language.ADA
        assert detect_language("src/main.adb") == Language.ADA
        assert detect_language("src/main.ads") == Language.ADA

    def test_markdown_files(self):
        assert detect_language("docs/README.md") == Language.MARKDOWN
        assert detect_language("docs/guide.mdx") == Language.MARKDOWN
        assert detect_language("docs/index.rst") == Language.MARKDOWN

    def test_unknown_files(self):
        assert detect_language("config.json") == Language.UNKNOWN
        assert detect_language("Makefile") == Language.UNKNOWN
        assert detect_language("Dockerfile") == Language.UNKNOWN


class TestIsTestFile:
    def test_test_files(self):
        assert is_test_file("tests/test_main.py") is True
        assert is_test_file("src/test_user.py") is True
        assert is_test_file("src/user_test.py") is True
        assert is_test_file("tests/spec_main.py") is True
        assert is_test_file("src/user_spec.py") is True

    def test_non_test_files(self):
        assert is_test_file("src/main.py") is False
        assert is_test_file("app/user.py") is False
        assert is_test_file("docs/README.md") is False

    def test_case_insensitive(self):
        assert is_test_file("Tests/Test_Main.py") is True
        assert is_test_file("SRC/USER_TEST.PY") is True


class TestDetectLanguagesFromFiles:
    def test_mixed_files(self):
        files = [
            "src/main/java/UserService.java",
            "scripts/process_data.py",
            "docs/architecture.md",
            "tests/test_main.py",
        ]
        result = detect_languages_from_files(files)

        assert len(result) == 4
        assert result[0].language == Language.JAVA
        assert result[1].language == Language.PYTHON
        assert result[2].language == Language.MARKDOWN
        assert result[3].language == Language.PYTHON
        assert result[3].is_test is True

    def test_empty_list(self):
        result = detect_languages_from_files([])
        assert result == []

    def test_unknown_files(self):
        files = ["config.json", "Makefile"]
        result = detect_languages_from_files(files)
        assert all(f.language == Language.UNKNOWN for f in result)


class TestGetUniqueLanguages:
    def test_unique_languages(self):
        files = [
            FileChange(path="a.java", language=Language.JAVA),
            FileChange(path="b.py", language=Language.PYTHON),
            FileChange(path="c.java", language=Language.JAVA),
            FileChange(path="d.md", language=Language.MARKDOWN),
        ]
        result = get_unique_languages(files)
        assert result == [Language.JAVA, Language.PYTHON, Language.MARKDOWN]

    def test_excludes_unknown(self):
        files = [
            FileChange(path="a.java", language=Language.JAVA),
            FileChange(path="b.json", language=Language.UNKNOWN),
        ]
        result = get_unique_languages(files)
        assert result == [Language.JAVA]

    def test_empty_list(self):
        result = get_unique_languages([])
        assert result == []

    def test_preserves_order(self):
        files = [
            FileChange(path="a.py", language=Language.PYTHON),
            FileChange(path="b.java", language=Language.JAVA),
            FileChange(path="c.cpp", language=Language.CPP),
        ]
        result = get_unique_languages(files)
        assert result == [Language.PYTHON, Language.JAVA, Language.CPP]
