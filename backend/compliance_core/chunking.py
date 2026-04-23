import re

# Max characters per stored chunk (embedding row).
_MAX_CHARS = 2400
_JOIN = "\n\n"


def _paragraphs(text: str) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", t) if b.strip()]
    if len(blocks) == 1 and "\n" in blocks[0] and "\n\n" not in t:
        return [L.strip() for L in blocks[0].splitlines() if L.strip()]
    return blocks


def _split_too_long(block: str, m: int) -> list[str]:
    """If one paragraph exceeds m chars, cut into pieces (word boundary when we can, else m)."""
    s = block.strip()
    if not s:
        return []
    if len(s) <= m:
        return [s]
    out: list[str] = []
    while len(s) > m:
        head = s[:m]
        sp = head.rfind(" ")
        if sp < m // 4 or sp < 0:
            sp = m
        else:
            sp = sp + 1
        out.append(s[:sp].rstrip())
        s = s[sp:].lstrip()
    if s:
        out.append(s)
    return out


def chunk_text(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    """
    1) Split on paragraph breaks (blank line, or all lines if no blank line).
    2) Split any too-long block so no piece is above max_chars (default 2400).
    3) Merge small blocks with a blank line until the next would exceed max_chars.
    """
    parts: list[str] = []
    for p in _paragraphs(text):
        parts.extend(_split_too_long(p, max_chars))
    if not parts:
        return []
    out: list[str] = []
    cur: list[str] = []
    n = 0
    for p in parts:
        add = len(p) + (len(_JOIN) if cur else 0)
        if cur and n + add > max_chars:
            out.append(_JOIN.join(cur))
            cur, n = [p], len(p)
        else:
            n += add
            cur.append(p)
    if cur:
        out.append(_JOIN.join(cur))
    return out
