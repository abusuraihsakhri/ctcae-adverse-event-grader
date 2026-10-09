"""Regression and boundary tests for explicitly supported NCI CTCAE v5.0 rules."""
import csv
import math
import pytest

from ctcae_grading import TERMS, grade_lab_event, main, process_ctcae_csv


@pytest.mark.parametrize("term,lln,bounds", [
    ("Neutrophil count decreased", 1800, (1500, 1000, 500)),
    ("Platelet count decreased", 150000, (75000, 50000, 25000)),
])
def test_grade_boundaries(term, lln, bounds):
    first, second, third = bounds
    for value, grade in [
        (lln, None), (lln + 10, None), (lln - 1, 1),
        (first, 1), (first - 1, 2),
        (second, 2), (second - 1, 3),
        (third, 3), (third - 1, 4), (0, 4),
    ]:
        result = grade_lab_event(term, value, lln)
        assert result["grade"] == grade
        assert result["ctcae_version"] == "5.0"
        assert result["unit"] == "/uL"


@pytest.mark.parametrize("term,value,lln", [
    ("Anemia", 8, 12),
    ("Platelet count decreased", -1, 150000),
    ("Platelet count decreased", 50, 0),
    ("Platelet count decreased", 50, 75000),
    ("Neutrophil count decreased", 900, 1500),
    ("Neutrophil count decreased", float("nan"), 1800),
    ("Neutrophil count decreased", float("inf"), 1800),
    ("Neutrophil count decreased", "missing", 1800),
])
def test_rejects_invalid_measurements(term, value, lln):
    with pytest.raises(ValueError):
        grade_lab_event(term, value, lln)


def test_batch_roundtrip(tmp_path):
    source = tmp_path / "in.csv"
    result = tmp_path / "sub" / "out.csv"
    source.write_text(
        "case,term,value,lln\n"
        "C1,Neutrophil count decreased,999,1800\n"
        "C2,Platelet count decreased,150000,150000\n",
        encoding="utf-8",
    )
    assert process_ctcae_csv(str(source), str(result)) == 2
    with result.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [r["ctcae_grade"] for r in rows] == ["3", ""]
    assert all(r["ctcae_version"] == "5.0" for r in rows)


@pytest.mark.parametrize("contents", [
    "", "a,b,c\n1,2,3\n",
    "term,value,lln,lln\na,2,3,4\n",
    "term,value,lln\nNeutrophil count decreased,not-a-number,1800\n",
    "term,value,lln\nNeutrophil count decreased,200,1800,extra\n",
    "term,value,lln,ctcae_grade\na,2,3,2\n",
])
def test_batch_fails_closed(tmp_path, contents):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError):
        process_ctcae_csv(str(source), str(target))
    assert not target.exists()


def test_cli_single(capsys):
    assert main(["grade", "--term", "Neutrophil count decreased", "--value", "500", "--lln", "1800"]) == 0
    assert '"grade": 3' in capsys.readouterr().out
