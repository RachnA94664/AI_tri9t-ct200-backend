import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional
from app.services.text_normalize import normalize_text

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
MAX_HEADING_WORDS = 15


@dataclass
class RawBlock:
    """One text block from PyMuPDF inspection: size, bold flag, text, page order."""
    text: str
    size: float
    bold: bool
    order_index: int


@dataclass
class TreeNode:
    heading_number: Optional[str]
    heading_text: str
    level: int
    order_index: int
    body_lines: List[str] = field(default_factory=list)
    parent: Optional["TreeNode"] = None
    children: List["TreeNode"] = field(default_factory=list)

    @property
    def body_text(self) -> str:
        return normalize_text("\n".join(self.body_lines))

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.body_text.encode("utf-8")).hexdigest()


def is_heading(block: RawBlock) -> Optional[re.Match]:
    """A block is a heading iff it's bold, short, and starts with a
    numbering prefix. This is the regex-first strategy: font size alone
    is ambiguous (2.1.1.1 headings and table header cells are both bold 11pt).
    """
    if not block.bold:
        return None
    text = normalize_text(block.text)
    if len(text.split()) > MAX_HEADING_WORDS:
        return None
    return HEADING_RE.match(text)


def build_tree(blocks: List[RawBlock], title_text: str) -> TreeNode:
    """
    Builds the hierarchy using heading_number prefixes for parenting
    (NOT document order — order and numbering can disagree, e.g. section
    3.4 appearing physically before 3.3 in this document).
    order_index still reflects physical position, for faithful rendering.
    """
    root = TreeNode(heading_number=None, heading_text=title_text, level=0, order_index=0)

    # stack of currently-open ancestors, indexed by level
    open_by_level = {0: root}
    current: TreeNode = root

    for block in blocks:
        match = is_heading(block)
        if match is None:
            # body content — attach to whatever node is currently "open"
            current.body_lines.append(block.text)
            continue

        number, heading_text = match.group(1), match.group(2)
        level = number.count(".") + 1
        node = TreeNode(
            heading_number=number,
            heading_text=normalize_text(heading_text),
            level=level,
            order_index=block.order_index,
        )

        # find parent: the deepest currently-open ancestor at level-1,
        # derived from the NUMERIC prefix, not from "the last heading seen"
        parent_number = ".".join(number.split(".")[:-1])
        parent = _find_ancestor_by_number(root, parent_number)

        node.parent = parent
        parent.children.append(node)
        open_by_level[level] = node
        current = node

    return root


def _find_ancestor_by_number(root: TreeNode, number: str) -> TreeNode:
    """Find the nearest EXISTING ancestor by numeric prefix. Handles two
    real cases found in this document: (1) out-of-order siblings like
    3.4-before-3.3, solved by matching on number not stream order, and
    (2) skipped numbering levels like 2.1.1.1 appearing with no 2.1.1
    node in between — solved by walking up the prefix chain (2.1.1 ->
    2.1 -> 2 -> root) until we find a node that actually exists, rather
    than requiring an exact one-level-up match.
    """
    def find_exact(n: str) -> Optional[TreeNode]:
        if n == "":
            return root
        stack = [root]
        while stack:
            node = stack.pop()
            if node.heading_number == n:
                return node
            stack.extend(node.children)
        return None

    segments = number.split(".")
    while segments:
        candidate = ".".join(segments)
        found = find_exact(candidate)
        if found is not None:
            return found
        segments = segments[:-1]  # drop last segment, try shorter prefix

    return root