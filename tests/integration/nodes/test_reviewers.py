from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.models import FileChange, Language, ReviewSeverity
from app.graph.nodes.reviewers.ada import AdaReviewer
from app.graph.nodes.reviewers.cpp import CppReviewer
from app.graph.nodes.reviewers.docs import DocsReviewer
from app.graph.nodes.reviewers.java import JavaReviewer
from app.graph.nodes.reviewers.python import PythonReviewer


class TestPythonReviewer:
    def test_language(self):
        reviewer = PythonReviewer(llm_client=MagicMock())
        assert reviewer.language == Language.PYTHON

    def test_parse_llm_response(self):
        reviewer = PythonReviewer(llm_client=MagicMock())
        response = """
        [WARNING] src/main.py:42 - Missing type hint
        [CRITICAL] src/utils.py:10 - Unused import
        [INFO] src/models.py:5 - Good use of dataclass
        """
        issues = reviewer.parse_llm_response(response)
        assert len(issues) == 3
        assert issues[0].severity == ReviewSeverity.WARNING
        assert issues[0].file == "src/main.py"
        assert issues[0].line == 42
        assert issues[1].severity == ReviewSeverity.CRITICAL
        assert issues[2].severity == ReviewSeverity.INFO

    def test_parse_severity(self):
        reviewer = PythonReviewer(llm_client=MagicMock())
        assert reviewer._parse_severity("CRITICAL") == ReviewSeverity.CRITICAL
        assert reviewer._parse_severity("WARNING") == ReviewSeverity.WARNING
        assert reviewer._parse_severity("INFO") == ReviewSeverity.INFO
        assert reviewer._parse_severity("UNKNOWN") == ReviewSeverity.INFO

    @pytest.mark.asyncio
    async def test_review(self):
        mock_llm = AsyncMock()
        mock_llm.review = AsyncMock(return_value="[WARNING] test.py:1 - Issue found")
        reviewer = PythonReviewer(llm_client=mock_llm)
        files = [FileChange(path="test.py", language=Language.PYTHON)]
        result = await reviewer.review(files, "+new line")
        assert result.language == Language.PYTHON
        assert len(result.issues) == 1
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_review_with_critical(self):
        mock_llm = AsyncMock()
        mock_llm.review = AsyncMock(return_value="[CRITICAL] test.py:1 - Critical issue")
        reviewer = PythonReviewer(llm_client=mock_llm)
        files = [FileChange(path="test.py", language=Language.PYTHON)]
        result = await reviewer.review(files, "+new line")
        assert result.passed is False


class TestJavaReviewer:
    def test_language(self):
        reviewer = JavaReviewer(llm_client=MagicMock())
        assert reviewer.language == Language.JAVA

    def test_parse_llm_response(self):
        reviewer = JavaReviewer(llm_client=MagicMock())
        response = "[WARNING] src/UserService.java:25 - Method too long"
        issues = reviewer.parse_llm_response(response)
        assert len(issues) == 1
        assert issues[0].file == "src/UserService.java"


class TestCppReviewer:
    def test_language(self):
        reviewer = CppReviewer(llm_client=MagicMock())
        assert reviewer.language == Language.CPP

    def test_parse_llm_response(self):
        reviewer = CppReviewer(llm_client=MagicMock())
        response = "[INFO] src/main.cpp:10 - Use const reference"
        issues = reviewer.parse_llm_response(response)
        assert len(issues) == 1


class TestAdaReviewer:
    def test_language(self):
        reviewer = AdaReviewer(llm_client=MagicMock())
        assert reviewer.language == Language.ADA

    def test_parse_llm_response(self):
        reviewer = AdaReviewer(llm_client=MagicMock())
        response = "[WARNING] src/main.adb:15 - Missing comments"
        issues = reviewer.parse_llm_response(response)
        assert len(issues) == 1


class TestDocsReviewer:
    def test_language(self):
        reviewer = DocsReviewer(llm_client=MagicMock())
        assert reviewer.language == Language.MARKDOWN

    def test_parse_llm_response(self):
        reviewer = DocsReviewer(llm_client=MagicMock())
        response = "[WARNING] docs/README.md:10 - Typo found"
        issues = reviewer.parse_llm_response(response)
        assert len(issues) == 1
