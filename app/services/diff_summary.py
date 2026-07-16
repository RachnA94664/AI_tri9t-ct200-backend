import difflib


def generate_diff_summary(old_text: str, new_text: str, context_lines: int = 1) -> str:
    """
    Uses Python's stdlib difflib (no extra dependency) to produce a compact,
    human-readable unified diff. Good enough for 'what changed' at a glance;
    NOT a semantic diff — it has no idea that '40 mmHg' -> '30 mmHg' is a
    meaningful spec change vs. a cosmetic wording tweak. See approach.md
    limitations section.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile="v1", tofile="v2",
        n=context_lines, lineterm="",
    )
    diff_lines = list(diff)
    if not diff_lines:
        return "No textual differences."
    return "\n".join(diff_lines)