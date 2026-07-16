import re

# Map the specific mis-decoded sequences observed in this PDF's font encoding.
# This is intentionally a fixed table for THIS document, not a generic
# Unicode-repair library — the assignment explicitly says don't over-build
# a generic parser.
_REPLACEMENTS = {
    "\u2261\u00bc\u00fc": "fi",   # broken "fi" ligature (∩¼ü)
    "\u0393\u00c7\u00f4": "\u2013",  # en dash (ΓÇô)
    "\u0393\u00c7\u00f6": "\u2014",  # em dash (ΓÇö)
    "\u0393\u00c7\u00e6": "\u2013",  # non-breaking hyphen variant (ΓÇæ) -> en dash
    "\u252c\u25b2": "\u00b1",     # plus-minus (┬▒)
}


def normalize_text(raw: str) -> str:
    text = raw
    for bad, good in _REPLACEMENTS.items():
        text = text.replace(bad, good)
    # collapse whitespace from multi-line font blocks being joined
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()