from app.llm.prompts import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_PROMPT,
    JAVA_REVIEWER_PROMPT,
    PYTHON_REVIEWER_PROMPT,
    CPP_REVIEWER_PROMPT,
    ADA_REVIEWER_PROMPT,
    DOCS_REVIEWER_PROMPT,
    COMPARISON_PROMPT,
    DOC_CODE_ALIGNMENT_PROMPT,
)


class TestPrompts:
    def test_judge_system_prompt_exists(self):
        assert JUDGE_SYSTEM_PROMPT is not None
        assert len(JUDGE_SYSTEM_PROMPT) > 0
        assert "Lead Software Architect" in JUDGE_SYSTEM_PROMPT

    def test_judge_user_prompt_exists(self):
        assert JUDGE_USER_PROMPT is not None
        assert len(JUDGE_USER_PROMPT) > 0
        assert "{all_reports}" in JUDGE_USER_PROMPT

    def test_java_reviewer_prompt_exists(self):
        assert JAVA_REVIEWER_PROMPT is not None
        assert len(JAVA_REVIEWER_PROMPT) > 0
        assert "Google Java Style" in JAVA_REVIEWER_PROMPT
        assert "{diff}" in JAVA_REVIEWER_PROMPT

    def test_python_reviewer_prompt_exists(self):
        assert PYTHON_REVIEWER_PROMPT is not None
        assert len(PYTHON_REVIEWER_PROMPT) > 0
        assert "PEP 8" in PYTHON_REVIEWER_PROMPT
        assert "{diff}" in PYTHON_REVIEWER_PROMPT

    def test_cpp_reviewer_prompt_exists(self):
        assert CPP_REVIEWER_PROMPT is not None
        assert len(CPP_REVIEWER_PROMPT) > 0
        assert "Google C++ Style" in CPP_REVIEWER_PROMPT
        assert "{diff}" in CPP_REVIEWER_PROMPT

    def test_ada_reviewer_prompt_exists(self):
        assert ADA_REVIEWER_PROMPT is not None
        assert len(ADA_REVIEWER_PROMPT) > 0
        assert "{diff}" in ADA_REVIEWER_PROMPT

    def test_docs_reviewer_prompt_exists(self):
        assert DOCS_REVIEWER_PROMPT is not None
        assert len(DOCS_REVIEWER_PROMPT) > 0
        assert "{diff}" in DOCS_REVIEWER_PROMPT

    def test_comparison_prompt_exists(self):
        assert COMPARISON_PROMPT is not None
        assert len(COMPARISON_PROMPT) > 0
        assert "{previous_review}" in COMPARISON_PROMPT
        assert "{current_review}" in COMPARISON_PROMPT

    def test_doc_code_alignment_prompt_exists(self):
        assert DOC_CODE_ALIGNMENT_PROMPT is not None
        assert len(DOC_CODE_ALIGNMENT_PROMPT) > 0
        assert "{code_changes}" in DOC_CODE_ALIGNMENT_PROMPT
        assert "{doc_changes}" in DOC_CODE_ALIGNMENT_PROMPT

    def test_judge_user_prompt_formatting(self):
        formatted = JUDGE_USER_PROMPT.format(all_reports="Test report")
        assert "Test report" in formatted
        assert "PRism" in formatted

    def test_java_reviewer_prompt_formatting(self):
        formatted = JAVA_REVIEWER_PROMPT.format(diff="Test diff")
        assert "Test diff" in formatted

    def test_python_reviewer_prompt_formatting(self):
        formatted = PYTHON_REVIEWER_PROMPT.format(diff="Test diff")
        assert "Test diff" in formatted

    def test_cpp_reviewer_prompt_formatting(self):
        formatted = CPP_REVIEWER_PROMPT.format(diff="Test diff")
        assert "Test diff" in formatted

    def test_ada_reviewer_prompt_formatting(self):
        formatted = ADA_REVIEWER_PROMPT.format(diff="Test diff")
        assert "Test diff" in formatted

    def test_docs_reviewer_prompt_formatting(self):
        formatted = DOCS_REVIEWER_PROMPT.format(diff="Test diff")
        assert "Test diff" in formatted

    def test_comparison_prompt_formatting(self):
        formatted = COMPARISON_PROMPT.format(
            previous_review="Previous", current_review="Current"
        )
        assert "Previous" in formatted
        assert "Current" in formatted

    def test_doc_code_alignment_prompt_formatting(self):
        formatted = DOC_CODE_ALIGNMENT_PROMPT.format(
            code_changes="Code", doc_changes="Docs"
        )
        assert "Code" in formatted
        assert "Docs" in formatted