import json

import pytest

from app.eval.benchmark import BenchmarkCase, BenchmarkDataset, load_benchmark, save_benchmark


class TestBenchmarkCase:
    def test_creation(self):
        case = BenchmarkCase(
            case_id="test-001",
            files_changed="app.py",
            diff="+new line",
            expected_findings=[{"finding": "x"}],
            language="python",
            tags=["security"],
        )
        assert case.case_id == "test-001"
        assert case.language == "python"
        assert "security" in case.tags

    def test_default_values(self):
        case = BenchmarkCase(case_id="test-002", files_changed="a.py", diff="+x")
        assert case.expected_findings == []
        assert case.language is None
        assert case.tags == []


class TestBenchmarkDataset:
    def test_filter_by_language(self):
        cases = [
            BenchmarkCase(case_id="1", files_changed="a.py", diff="+x", language="python"),
            BenchmarkCase(case_id="2", files_changed="b.java", diff="+y", language="java"),
        ]
        dataset = BenchmarkDataset(name="test", cases=cases)
        filtered = dataset.filter_by_language("python")
        assert len(filtered.cases) == 1
        assert filtered.cases[0].language == "python"

    def test_filter_by_tag(self):
        cases = [
            BenchmarkCase(case_id="1", files_changed="a.py", diff="+x", tags=["security"]),
            BenchmarkCase(case_id="2", files_changed="b.py", diff="+y", tags=["performance"]),
        ]
        dataset = BenchmarkDataset(name="test", cases=cases)
        filtered = dataset.filter_by_tag("security")
        assert len(filtered.cases) == 1

    def test_split(self):
        cases = [BenchmarkCase(case_id=str(i), files_changed="a.py", diff="+x") for i in range(10)]
        dataset = BenchmarkDataset(name="test", cases=cases)
        train, test = dataset.split(train_ratio=0.8)
        assert len(train.cases) == 8
        assert len(test.cases) == 2

    def test_split_preserves_metadata(self):
        dataset = BenchmarkDataset(name="test", version="2.0", description="desc", source="src")
        train, test = dataset.split()
        assert train.version == "2.0"
        assert test.source == "src"


class TestLoadBenchmark:
    def test_load_json_list(self, tmp_path):
        data = [{"case_id": "1", "files_changed": "a.py", "diff": "+x"}]
        path = tmp_path / "benchmark.json"
        path.write_text(json.dumps(data))
        dataset = load_benchmark(path)
        assert len(dataset.cases) == 1
        assert dataset.name == "benchmark"

    def test_load_json_object(self, tmp_path):
        data = {"name": "custom", "cases": [{"case_id": "1", "files_changed": "a.py", "diff": "+x"}]}
        path = tmp_path / "benchmark.json"
        path.write_text(json.dumps(data))
        dataset = load_benchmark(path)
        assert dataset.name == "custom"
        assert len(dataset.cases) == 1

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_benchmark("/nonexistent/path.json")


class TestSaveBenchmark:
    def test_save_and_load(self, tmp_path):
        cases = [BenchmarkCase(case_id="1", files_changed="a.py", diff="+x", language="python")]
        dataset = BenchmarkDataset(name="test", cases=cases)
        path = tmp_path / "benchmark.json"
        save_benchmark(dataset, path)
        loaded = load_benchmark(path)
        assert loaded.name == "test"
        assert len(loaded.cases) == 1
        assert loaded.cases[0].language == "python"

    def test_save_creates_directories(self, tmp_path):
        dataset = BenchmarkDataset(name="test")
        path = tmp_path / "subdir" / "benchmark.json"
        save_benchmark(dataset, path)
        assert path.exists()
