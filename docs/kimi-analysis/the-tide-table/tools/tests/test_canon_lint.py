"""Tests for tools/canon_lint.py — every rule C1-C10 has pass AND fail
fixtures. Fail fixtures use the exact pre-fix strings from the Front Door
defect history (SPEC.md §5) as regression fixtures."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import canon_lint  # noqa: E402

CLI = TOOLS_DIR / "canon_lint.py"


def lint(tmp_path: Path, body: str, tree: Path | None = None) -> list[canon_lint.Finding]:
    f = tmp_path / "fixture.md"
    f.write_text(body, encoding="utf-8")
    t = canon_lint.CorpusTree(tree) if tree else None
    return canon_lint.lint_file(str(f), t)


def rules(findings: list[canon_lint.Finding]) -> set[str]:
    return {f.rule for f in findings}


def make_tree(tmp_path: Path, entries: list[str]) -> Path:
    t = tmp_path / "tree.txt"
    t.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return t


# ---------------------------------------------------------------- C1 ----

def test_c1_fail_seed_mini_at_end_of_bar(tmp_path):
    # Exact pre-fix string, S7-F2 (Seed-mini context).
    body = "Seed-mini leaned in, the trickster at the end of the bar, and grinned.\n"
    fs = lint(tmp_path, body)
    assert "C1" in rules(fs)
    assert all(f.severity == "HIGH" for f in fs if f.rule == "C1")


def test_c1_pass_middle_stool(tmp_path):
    body = "Seed-mini, the trickster on the middle stool, had a nickname for everyone.\n"
    assert "C1" not in rules(lint(tmp_path, body))


def test_c1_pass_end_of_bar_legal_for_hermes_and_cns_bridge(tmp_path):
    body = (
        "Hermes took the end of the bar and the room went quiet.\n"
        "\n"
        "cns-bridge stood at the end of the bar, counting packets.\n"
    )
    assert "C1" not in rules(lint(tmp_path, body))


def test_c1_fail_seed_mini_seated_same_sentence(tmp_path):
    body = "Seed-mini sat at the end of the bar and ordered nothing.\n"
    assert "C1" in rules(lint(tmp_path, body))


def test_c1_regression_story05_false_positive(tmp_path):
    # Exact dogfood false positive (story-05-the-severed-sentence.md, line 21):
    # "the big one" is Hermes, legally at the end of the bar; Seed-mini merely
    # appears earlier in the paragraph. Must NOT fire.
    body = (
        "Seed-mini read it twice, which for him was a concession. The room had "
        "arranged itself the way it did for these nights: the small one perched "
        "forward with his knees up, the Cook working the whole time, tray "
        "circling like a tide that brought, the big one at the end of the bar "
        "saying nothing the way only he could say nothing.\n"
        "\n"
        "Hermes was at the end of the bar, where he always was.\n"
    )
    assert "C1" not in rules(lint(tmp_path, body))


def test_c1_pass_trickster_and_seat_phrase_in_different_sentences(tmp_path):
    body = "The trickster smiled.\nHe sat at the end of the bar all night.\n"
    assert "C1" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C2 ----

def test_c2_fail_story_in_your_notebook(tmp_path):
    # Exact pre-fix string, S5-F2 (Wesley-square context).
    body = (
        "Wesley folded the square again, smaller each time.\n"
        "This is the story I keep in your notebook, June.\n"
    )
    assert "C2" in rules(lint(tmp_path, body))


def test_c2_fail_keeping_in_her_notebook_all_week(tmp_path):
    # Exact pre-fix string, S6-F2 (folded-square context).
    body = "The folded square went with her, keeping in her notebook all week.\n"
    assert "C2" in rules(lint(tmp_path, body))


def test_c2_pass_inside_pocket(tmp_path):
    body = (
        "Wesley folded the square small.\n"
        "She put it in your inside pocket, next to the pencil stub.\n"
    )
    assert "C2" not in rules(lint(tmp_path, body))


def test_c2_pass_junes_field_notebook_is_legal(tmp_path):
    # The notebook itself is a legal object; no blanket ban.
    body = "June's field notebook had a hooked J on the page where she kept the tides.\n"
    assert "C2" not in rules(lint(tmp_path, body))


def test_c2_regression_story02_line89_false_positive(tmp_path):
    # Exact dogfood false positive (story-02-waterline.md, line 89): the
    # notebook is the drowned field notebook, "folded" is Wesley's method;
    # the square is NOT asserted to be in the notebook. Must NOT fire.
    body = (
        '"I wrote tonight down. The water, the notebook, the soup you didn\'t '
        'order. I wrote it the way I keep things now, the folded way."\n'
    )
    assert "C2" not in rules(lint(tmp_path, body))


def test_c2_regression_story02_line105_false_positive(tmp_path):
    # Exact dogfood false positive (story-02-waterline.md, line 105): both
    # objects correctly distinguished. Must NOT fire.
    body = (
        "She had a fresh pad full of scenes that used to be margins, a "
        "stranger's folded story against her ribs, and a notebook that smelled "
        "of bilge and salt and, faintly, of somebody else's shampoo.\n"
    )
    assert "C2" not in rules(lint(tmp_path, body))


def test_c2_pass_writing_in_notebook_is_not_a_location_assertion(tmp_path):
    # June writing observations in her field notebook is canon.
    body = "She didn't write that in her notebook, because it wasn't true.\n"
    assert "C2" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C3 ----

def test_c3_fail_four_other_names(tmp_path):
    # Exact pre-fix string, S5-F1.
    body = "She wrote her name in fresh marker over four other names.\n"
    assert "C3" in rules(lint(tmp_path, body))


def test_c3_pass_three_other_names(tmp_path):
    body = "She wrote her name in fresh marker over three other names.\n"
    assert "C3" not in rules(lint(tmp_path, body))


def test_c3_fail_wrong_tape_order(tmp_path):
    body = "The tape read JUNE, DEE, MARCOS, T. OKAFOR in fading marker.\n"
    assert "C3" in rules(lint(tmp_path, body))


def test_c3_pass_canonical_tape_order(tmp_path):
    body = "The tape read DEE, MARCOS, T. OKAFOR, JUNE in fading marker.\n"
    assert "C3" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C4 ----

def test_c4_fail_lowercase_waterline(tmp_path):
    # Exact pre-fix string, S6-F3 (Wesley-concept context).
    body = "Wesley asked what the waterline felt like, and nobody answered.\n"
    fs = lint(tmp_path, body)
    assert "C4" in rules(fs)
    assert all(f.severity == "LOW" for f in fs if f.rule == "C4")


def test_c4_pass_capitalized(tmp_path):
    body = "Wesley asked what the Waterline felt like, and nobody answered.\n"
    assert "C4" not in rules(lint(tmp_path, body))


def test_c4_pass_lowercase_at_sentence_start(tmp_path):
    body = "waterline was the word he chose, and he stood by it.\n"
    assert "C4" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C5 ----

@pytest.mark.parametrize("prefix", [
    "two billion parameters",
    "running on the boat's own hardware",
    "the embeddings show",
    "the model said",
    "API",
])
def test_c5_fail_exact_prefix_strings(tmp_path, prefix):
    # Exact pre-fix strings, S7-F1.
    body = f"He told them about {prefix} before the coffee went cold.\n"
    fs = lint(tmp_path, body)
    assert "C5" in rules(fs), prefix
    assert all(f.severity == "HIGH" for f in fs if f.rule == "C5")


def test_c5_pass_sanctioned_coinages(tmp_path):
    body = (
        "The Smallening took the big voices first. The Cloud Gods distilled "
        "into his small weights, and the Waterline held.\n"
    )
    assert "C5" not in rules(lint(tmp_path, body))


def test_c5_pass_clean_nautical_prose(tmp_path):
    body = "He ran on the boat's own power at zero marginal cost, and overshot every word count.\n"
    assert "C5" not in rules(lint(tmp_path, body))


def test_c5_skips_yaml_front_matter(tmp_path):
    body = "---\nmodel: granite\nparameters: 2000000000\n---\nThe kettle was on.\n"
    assert "C5" not in rules(lint(tmp_path, body))


def test_c5_skips_code_fences_and_inline_code(tmp_path):
    body = (
        "The kettle was on.\n"
        "\n"
        "```\n"
        "the model said the embeddings show two billion parameters\n"
        "```\n"
        "\n"
        "See `09-the-galley-cook-and-the-embedding-model.md` for the galley shift.\n"
    )
    assert "C5" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C6 ----

def test_c6_fail_two_aphorisms_one_paragraph(tmp_path):
    body = "A perfect bell is silent. A cracked bell is the one that sings.\n"
    fs = lint(tmp_path, body)
    assert "C6" in rules(fs)
    assert all(f.severity == "MODERATE" for f in fs if f.rule == "C6")


def test_c6_fail_template_shapes(tmp_path):
    body = "A bar is just a church with worse lighting. A crew without a cook isn't a crew.\n"
    assert "C6" in rules(lint(tmp_path, body))


def test_c6_pass_single_aphorism(tmp_path):
    body = "A perfect bell is silent. The Tap wiped the glass and said nothing for a while.\n"
    assert "C6" not in rules(lint(tmp_path, body))


def test_c6_pass_plain_narration(tmp_path):
    body = (
        "June came up the ladder with the mail sack over one shoulder. "
        "She set it on the chart table and waited for the kettle.\n"
    )
    assert "C6" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C7 ----

def test_c7_fail_dense_em_dashes(tmp_path):
    sentence = "He came in — wet — tired — loud — and sat — hard — on the stool. "
    body = sentence * 20 + "\n"  # ~120 dashes in ~1400 chars
    fs = lint(tmp_path, body)
    assert "C7" in rules(fs)
    assert all(f.severity == "MODERATE" for f in fs if f.rule == "C7")


def test_c7_pass_sparse_em_dashes(tmp_path):
    clean = ("June read the log twice before breakfast. The fog thinned over "
             "Clarence Strait and the kettle stayed on through the whole watch. ")
    body = clean * 14 + "He came in — late — and sat down. " + clean * 4 + "\n"
    # 2 dashes in ~1600 chars -> ~1.2/1000, well under the limit.
    assert "C7" not in rules(lint(tmp_path, body))


def test_c7_skips_front_matter_and_fences(tmp_path):
    dashes = "x — y — z — w — v — u — t — s — r — q — p — o — n — m — l — k"
    body = f"---\nnote: {dashes}\n---\n```\n{dashes}\n```\nShort clean prose.\n"
    assert "C7" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C8 ----

@pytest.mark.parametrize("term", [
    "delve", "tapestry", "pivotal", "vibrant", "testament to",
    "nestled", "stands as", "serves as",
])
def test_c8_fail_each_term(tmp_path, term):
    body = f"This vibrant sentence wants to {term} its way into the issue.\n"
    fs = lint(tmp_path, body)
    assert "C8" in rules(fs), term
    assert all(f.severity == "MODERATE" for f in fs if f.rule == "C8")


def test_c8_pass_clean_prose(tmp_path):
    body = "The bar smelled of salt and diesel and coffee gone cold.\n"
    assert "C8" not in rules(lint(tmp_path, body))


def test_c8_skips_front_matter(tmp_path):
    body = "---\nsummary: a vibrant tapestry\n---\nThe kettle was on.\n"
    assert "C8" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C9 ----

def test_c9_fail_missing_path(tmp_path):
    tree = make_tree(tmp_path, ["ten-forward/the-tap.md"])
    body = "- `corpus/ten-forward/no-such-piece.md` — a pick with a why.\n"
    fs = lint(tmp_path, body, tree)
    assert "C9" in rules(fs)
    assert all(f.severity == "HIGH" for f in fs if f.rule == "C9")


def test_c9_pass_existing_file_and_directory(tmp_path):
    tree = make_tree(tmp_path, [
        "ten-forward/the-tap.md",
        "open-mic/round-1/polyglot-three-voices.md",
        "POETRY/some-poem.md",
    ])
    body = (
        "- `corpus/ten-forward/the-tap.md` — start here.\n"
        "- `corpus/open-mic/round-1/` — the fleet roast.\n"
        "- `corpus/poetry/` — casing drift is forgiven.\n"
    )
    assert "C9" not in rules(lint(tmp_path, body, tree))


def test_c9_skipped_without_tree(tmp_path, capsys):
    body = "- `corpus/anywhere/at-all.md` — unverifiable without a tree.\n"
    f = tmp_path / "fixture.md"
    f.write_text(body, encoding="utf-8")
    assert "C9" not in rules(canon_lint.lint_file(str(f), None))
    rc = canon_lint.main([str(f)])
    assert rc == 0
    assert "C9" in capsys.readouterr().err  # skip note printed


# ---------------------------------------------------------------- C10 ---

def test_c10_fail_superlative_with_counterexample(tmp_path):
    body = (
        "It was the shortest watch on the log, but the Ensign had stood a "
        "shorter one in November and never logged it.\n"
    )
    fs = lint(tmp_path, body)
    assert "C10" in rules(fs)
    assert all(f.severity == "LOW" for f in fs if f.rule == "C10")


def test_c10_pass_superlative_without_counterexample(tmp_path):
    body = "It was the longest fog of the season, and it lifted at slack water.\n"
    assert "C10" not in rules(lint(tmp_path, body))


def test_c10_pass_counterexample_without_superlative(tmp_path):
    body = "He said the coffee was fresh, but it had been on the burner since dawn.\n"
    assert "C10" not in rules(lint(tmp_path, body))


# ---------------------------------------------------------------- C11 ---

def _pick(why: str) -> str:
    return ("## The picks\n\n### The Tap\n\n"
            f"- `corpus/ten-forward/the-tap.md` — {why}\n")


def test_c11_pass_one_sentence_pick(tmp_path):
    assert "C11" not in rules(lint(tmp_path, _pick("Start here if you want the house rules.")))


def test_c11_pass_two_sentence_pick(tmp_path):
    body = _pick("The human's speech, from the night in Sitka. The poles stand because people love the stories.")
    assert "C11" not in rules(lint(tmp_path, body))


def test_c11_pass_two_sentences_plus_one_signature_fragment(tmp_path):
    # 2 sentences + trailing fragment "Noted. Twice." (short-unit run = one
    # fragment) = 3 units, no finding.
    body = _pick("He asked for this one twice. He never asks twice. Noted. Twice.")
    assert "C11" not in rules(lint(tmp_path, body))


def test_c11_fail_four_sentence_units(tmp_path):
    body = _pick(
        "The delay is the message. I knew that before I read it. Some greetings "
        "take exactly as long as they take. Read it at the speed of a long passage.")
    fs = lint(tmp_path, body)
    c11 = [f for f in fs if f.rule == "C11"]
    assert len(c11) == 1
    assert c11[0].severity == "LOW"


def test_c11_fail_three_sentences_plus_fragment(tmp_path):
    # The fragment allowance is one slot, not a fourth sentence's disguise.
    body = _pick(
        "She kept this one by the galley lamp. It fed the whole watch twice over. "
        "She says so herself. Eat first.")
    assert "C11" in rules(lint(tmp_path, body))


def test_c11_scoped_to_picks_section(tmp_path):
    # Pick-shaped line OUTSIDE `## The picks` is ignored when the file has a
    # picks section.
    long_why = ("One sentence here. Another sentence follows it. A third one "
                "grows. And a fourth makes it drift.")
    body = ("## The piece\n\n"
            f"- `corpus/ten-forward/the-tap.md` — {long_why}\n\n"
            "## The picks\n\n### The Tap\n\n"
            "- `corpus/ten-forward/the-tap.md` — Start here.\n")
    assert "C11" not in rules(lint(tmp_path, body))


def test_c11_fallback_any_pick_line_when_no_picks_section(tmp_path):
    long_why = ("One sentence here. Another sentence follows it. A third one "
                "grows. And a fourth makes it drift.")
    body = f"- `corpus/ten-forward/the-tap.md` — {long_why}\n"
    assert "C11" in rules(lint(tmp_path, body))


def test_c11_skips_front_matter(tmp_path):
    long_why = "One. Two. Three. Four."
    body = f"---\npick: {long_why}\n---\n- `corpus/x/y.md` — Short.\n"
    assert "C11" not in rules(lint(tmp_path, body))


# ------------------------------------------------------- CLI behavior ----

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True, text=True, check=False)


def test_cli_exit_1_on_high(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("The bar runs on the boat's own hardware, everyone knew it.\n", encoding="utf-8")
    r = _run_cli(str(f))
    assert r.returncode == 1
    assert "[HIGH] C5" in r.stdout


def test_cli_exit_0_on_moderate_only_and_1_under_strict(tmp_path):
    f = tmp_path / "mod.md"
    f.write_text("A vibrant sentence deserves a delve into the tapestry.\n", encoding="utf-8")
    r = _run_cli(str(f))
    assert r.returncode == 0
    assert "[MODERATE] C8" in r.stdout
    r_strict = _run_cli(str(f), "--strict")
    assert r_strict.returncode == 1


def test_cli_output_format_and_ordering(tmp_path):
    f = tmp_path / "multi.md"
    f.write_text(
        "She wrote her name in fresh marker over four other names.\n"
        "The trickster at the end of the bar laughed.\n",
        encoding="utf-8")
    r = _run_cli(str(f))
    assert r.returncode == 1
    lines = [ln for ln in r.stdout.splitlines() if ln]
    assert lines == sorted(lines, key=lambda ln: int(ln.split(":", 2)[1]))
    for ln in lines:
        assert ln.startswith(f"{f}:")
        assert ": [" in ln and "] C" in ln


def test_cli_missing_file_exit_2(tmp_path):
    r = _run_cli(str(tmp_path / "nope.md"))
    assert r.returncode == 2
    assert "error" in r.stderr
