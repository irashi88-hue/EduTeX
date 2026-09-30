"""Executable static contract checks for the EduTeX true/false renderer patch."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "src" / "edutex" / "build" / "html_renderer.py").read_text(encoding="utf-8")
FIXTURE = (ROOT / "assets" / "knowledge_models" / "true-false-demo.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "true_false_exercise.md").read_text(encoding="utf-8")


class TrueFalseContractTests(unittest.TestCase):
    def test_existing_exercise_paths_remain_present(self) -> None:
        for marker in (
            "_render_choice_exercise",
            "_render_short_answer",
            "_render_true_false_exercise",
        ):
            self.assertIn(marker, SOURCE)

    def test_true_false_uses_ordered_pairs_and_radio_controls(self) -> None:
        for marker in (
            "current_statement",
            "tf_invalid",
            'input type="radio"',
            "true-false-option",
            "true-false-check",
            "true-false-reset",
            "aria-labelledby",
            'aria-live="polite"',
            'data-answer="{html.escape(answer, quote=True)}"',
        ):
            self.assertIn(marker, SOURCE)

    def test_true_false_defers_feedback_until_check_and_supports_reset(self) -> None:
        self.assertIn('button.true-false-check', SOURCE)
        self.assertIn('button.true-false-reset', SOURCE)
        self.assertIn('row.dataset.selected === row.dataset.answer', SOURCE)
        self.assertIn('result.textContent = `${{correct}} / ${{rows.length}}`', SOURCE)
        self.assertIn('result.textContent = ""', SOURCE)

    def test_fixture_and_docs_define_localized_values_and_pairs(self) -> None:
        self.assertEqual(FIXTURE.count("statement:"), 3)
        self.assertEqual(FIXTURE.count("answer:"), 3)
        self.assertIn("answer: vero", FIXTURE)
        self.assertIn("answer: falso", FIXTURE)
        self.assertIn("answer: true", FIXTURE)
        self.assertIn("statement:", DOCS)
        self.assertIn("answer: false", DOCS)


if __name__ == "__main__":
    unittest.main()
