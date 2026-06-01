"""Wireframe schema → SVG renderer.

The LLM produces a JSON schema describing screens and their regions. This module
deterministically renders that schema into a single SVG containing multiple
screen frames laid out in a grid, ready to drag into Figma.

Schema (per screen):
    {
      "id": "S1",
      "name": "Screen title",
      "regions": [
        {"type": "header", "content": "...", "subtitle": "..."},
        {"type": "nav_bar", "items": [...], "active": "..."},
        {"type": "sidebar", "items": [...]},
        {"type": "form", "submit": "...", "fields": [
            {"label": "...", "kind": "input|textarea|dropdown|date|checkbox", "secret": false}
        ]},
        {"type": "table", "columns": [...], "row_count": 5},
        {"type": "list", "items": [...]},
        {"type": "card", "title": "...", "body": "...", "action": "..."},
        {"type": "button", "label": "...", "primary": true},
        {"type": "text_block", "content": "..."},
        {"type": "image_placeholder", "caption": "..."},
        {"type": "footer", "content": "..."}
      ]
    }
"""

# Canvas constants — desktop frame per screen, 3 per row, room for a title bar.
SCREEN_W = 1280
SCREEN_H = 800
SCREENS_PER_ROW = 3
GAP_X = 80
GAP_Y = 120
TITLE_BAR_H = 48
INNER_PAD = 32
COMPONENT_GAP = 16


def _esc(text: str) -> str:
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _clip(text: str, max_chars: int) -> str:
    s = str(text or "")
    return s if len(s) <= max_chars else s[: max_chars - 1].rstrip() + "…"


# ── Component renderers ─────────────────────────────────────────────────────────
# Each returns (svg_fragment, height_consumed).

def _header(r, x, y, w):
    h = 64
    title = _esc(_clip(r.get("content", "Header"), 60))
    sub = _esc(_clip(r.get("subtitle", ""), 80))
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#1f2937"/>',
        f'<text x="{x + 16}" y="{y + 28}" font-family="Inter, Arial" font-size="18" font-weight="700" fill="white">{title}</text>',
    ]
    if sub:
        parts.append(
            f'<text x="{x + 16}" y="{y + 50}" font-family="Inter, Arial" font-size="12" fill="#9ca3af">{sub}</text>'
        )
    return "\n".join(parts), h


def _nav_bar(r, x, y, w):
    h = 44
    items = r.get("items", []) or []
    active = r.get("active", "")
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f3f4f6" stroke="#e5e7eb"/>']
    cx = x + 16
    for item in items[:8]:
        label = _clip(item, 18)
        is_active = item == active
        text_w = max(60, 9 * len(label) + 24)
        if is_active:
            parts.append(
                f'<rect x="{cx}" y="{y + 8}" width="{text_w}" height="{h - 16}" rx="14" fill="#1f2937"/>'
            )
            parts.append(
                f'<text x="{cx + text_w / 2}" y="{y + 28}" text-anchor="middle" '
                f'font-family="Inter, Arial" font-size="13" fill="white">{_esc(label)}</text>'
            )
        else:
            parts.append(
                f'<text x="{cx + 12}" y="{y + 28}" font-family="Inter, Arial" font-size="13" fill="#4b5563">{_esc(label)}</text>'
            )
        cx += text_w + 8
    return "\n".join(parts), h


def _sidebar(r, x, y, w):
    items = r.get("items", []) or []
    item_h = 36
    h = max(item_h * len(items) + 16, item_h * 4)
    sidebar_w = min(220, w // 3)
    parts = [f'<rect x="{x}" y="{y}" width="{sidebar_w}" height="{h}" fill="#fafafa" stroke="#e5e7eb"/>']
    for i, item in enumerate(items[:10]):
        cy = y + 8 + i * item_h
        parts.append(
            f'<text x="{x + 16}" y="{cy + 22}" font-family="Inter, Arial" font-size="13" fill="#374151">{_esc(_clip(item, 24))}</text>'
        )
    # Right-side placeholder content next to the sidebar so the screen feels populated
    content_x = x + sidebar_w + 16
    content_w = w - sidebar_w - 16
    parts.append(
        f'<rect x="{content_x}" y="{y}" width="{content_w}" height="{h}" rx="6" '
        f'fill="white" stroke="#e5e7eb" stroke-dasharray="4 4"/>'
    )
    parts.append(
        f'<text x="{content_x + content_w / 2}" y="{y + h / 2 + 4}" text-anchor="middle" '
        f'font-family="Inter, Arial" font-size="12" fill="#9ca3af">main content</text>'
    )
    return "\n".join(parts), h


def _form(r, x, y, w):
    fields = r.get("fields", []) or []
    field_h = 56
    submit_h = 44
    pad_top = 8
    h = pad_top + len(fields) * field_h + submit_h + 8
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#e5e7eb"/>']
    cy = y + pad_top
    for f in fields:
        label = _esc(_clip(f.get("label", "Field"), 40))
        kind = f.get("kind", "input")
        secret = f.get("secret")
        parts.append(
            f'<text x="{x + 16}" y="{cy + 16}" font-family="Inter, Arial" font-size="12" fill="#4b5563">{label}</text>'
        )
        inner_y = cy + 22
        inner_h = 28
        if kind in ("textarea",):
            inner_h = 50
            h += inner_h - 28
        parts.append(
            f'<rect x="{x + 16}" y="{inner_y}" width="{w - 32}" height="{inner_h}" rx="4" '
            f'fill="#f9fafb" stroke="#d1d5db"/>'
        )
        if secret:
            parts.append(
                f'<text x="{x + 24}" y="{inner_y + 19}" font-family="monospace" font-size="13" fill="#9ca3af">••••••••</text>'
            )
        elif kind == "dropdown":
            parts.append(
                f'<text x="{x + w - 28}" y="{inner_y + 19}" font-family="Inter, Arial" font-size="13" fill="#9ca3af">▾</text>'
            )
        elif kind == "checkbox":
            parts.append(
                f'<rect x="{x + 24}" y="{inner_y + 6}" width="16" height="16" rx="3" fill="white" stroke="#9ca3af"/>'
            )
        cy += field_h + (inner_h - 28)
    # Submit button
    btn_label = _esc(_clip(r.get("submit", "Submit"), 24))
    btn_w = max(120, 10 * len(btn_label) + 32)
    btn_x = x + w - btn_w - 16
    parts.append(
        f'<rect x="{btn_x}" y="{cy}" width="{btn_w}" height="{submit_h - 8}" rx="6" fill="#2563eb"/>'
    )
    parts.append(
        f'<text x="{btn_x + btn_w / 2}" y="{cy + 24}" text-anchor="middle" '
        f'font-family="Inter, Arial" font-size="13" font-weight="600" fill="white">{btn_label}</text>'
    )
    return "\n".join(parts), h


def _table(r, x, y, w):
    columns = r.get("columns", []) or []
    row_count = int(r.get("row_count", 5) or 5)
    row_h = 32
    header_h = 36
    h = header_h + row_h * min(row_count, 8)
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#e5e7eb"/>']
    # Header row
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{header_h}" rx="6" fill="#f3f4f6"/>')
    col_w = w / max(len(columns), 1)
    for i, col in enumerate(columns):
        parts.append(
            f'<text x="{x + i * col_w + 12}" y="{y + 23}" font-family="Inter, Arial" '
            f'font-size="12" font-weight="600" fill="#374151">{_esc(_clip(col, 24))}</text>'
        )
    # Body rows (placeholder bars)
    for ri in range(min(row_count, 8)):
        ry = y + header_h + ri * row_h
        if ri > 0:
            parts.append(
                f'<line x1="{x}" y1="{ry}" x2="{x + w}" y2="{ry}" stroke="#f3f4f6"/>'
            )
        for i in range(len(columns)):
            parts.append(
                f'<rect x="{x + i * col_w + 12}" y="{ry + 10}" width="{col_w - 24}" height="10" rx="2" fill="#e5e7eb"/>'
            )
    return "\n".join(parts), h


def _list(r, x, y, w):
    items = r.get("items", []) or []
    item_h = 36
    h = max(item_h * min(len(items), 8) + 8, item_h)
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#e5e7eb"/>']
    for i, item in enumerate(items[:8]):
        cy = y + 6 + i * item_h
        parts.append(
            f'<circle cx="{x + 18}" cy="{cy + 16}" r="3" fill="#6b7280"/>'
        )
        parts.append(
            f'<text x="{x + 32}" y="{cy + 22}" font-family="Inter, Arial" font-size="13" fill="#374151">{_esc(_clip(item, 80))}</text>'
        )
    return "\n".join(parts), h


def _card(r, x, y, w):
    title = _esc(_clip(r.get("title", "Card"), 40))
    body = _clip(r.get("body", ""), 200)
    action = _esc(_clip(r.get("action", ""), 24))
    h = 120
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="white" stroke="#e5e7eb"/>']
    parts.append(
        f'<text x="{x + 16}" y="{y + 28}" font-family="Inter, Arial" font-size="15" font-weight="700" fill="#111827">{title}</text>'
    )
    # Body — naive line wrap on ~60 chars
    line_y = y + 52
    for line in [body[i:i + 60] for i in range(0, len(body), 60)][:3]:
        parts.append(
            f'<text x="{x + 16}" y="{line_y}" font-family="Inter, Arial" font-size="12" fill="#4b5563">{_esc(line)}</text>'
        )
        line_y += 16
    if action:
        btn_w = max(96, 10 * len(action) + 24)
        btn_x = x + w - btn_w - 16
        parts.append(
            f'<rect x="{btn_x}" y="{y + h - 38}" width="{btn_w}" height="28" rx="4" fill="#1f2937"/>'
        )
        parts.append(
            f'<text x="{btn_x + btn_w / 2}" y="{y + h - 19}" text-anchor="middle" '
            f'font-family="Inter, Arial" font-size="12" fill="white">{action}</text>'
        )
    return "\n".join(parts), h


def _button(r, x, y, w):
    label = _esc(_clip(r.get("label", "Button"), 40))
    primary = bool(r.get("primary"))
    h = 40
    btn_w = max(140, 10 * len(label) + 32)
    fill = "#2563eb" if primary else "white"
    stroke = "#2563eb" if primary else "#d1d5db"
    text_fill = "white" if primary else "#111827"
    parts = [
        f'<rect x="{x}" y="{y}" width="{btn_w}" height="{h - 4}" rx="6" fill="{fill}" stroke="{stroke}"/>',
        f'<text x="{x + btn_w / 2}" y="{y + 24}" text-anchor="middle" font-family="Inter, Arial" '
        f'font-size="13" font-weight="600" fill="{text_fill}">{label}</text>',
    ]
    return "\n".join(parts), h


def _text_block(r, x, y, w):
    text = str(r.get("content", "") or "")
    chars_per_line = max(20, w // 8)
    lines = []
    for paragraph in text.split("\n"):
        for i in range(0, max(len(paragraph), 1), chars_per_line):
            lines.append(paragraph[i:i + chars_per_line])
    lines = lines[:6]
    line_h = 18
    h = len(lines) * line_h + 8
    parts = []
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{x}" y="{y + 14 + i * line_h}" font-family="Inter, Arial" font-size="13" fill="#374151">{_esc(line)}</text>'
        )
    return "\n".join(parts), h


def _image_placeholder(r, x, y, w):
    caption = _esc(_clip(r.get("caption", "image"), 60))
    h = 180
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#f3f4f6" stroke="#d1d5db" stroke-dasharray="6 6"/>',
        f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y + h}" stroke="#d1d5db"/>',
        f'<line x1="{x + w}" y1="{y}" x2="{x}" y2="{y + h}" stroke="#d1d5db"/>',
        f'<text x="{x + w / 2}" y="{y + h - 12}" text-anchor="middle" '
        f'font-family="Inter, Arial" font-size="12" fill="#6b7280">{caption}</text>',
    ]
    return "\n".join(parts), h


def _footer(r, x, y, w):
    text = _esc(_clip(r.get("content", ""), 100))
    h = 36
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f9fafb" stroke="#e5e7eb"/>',
        f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" '
        f'font-family="Inter, Arial" font-size="11" fill="#6b7280">{text}</text>',
    ]
    return "\n".join(parts), h


_RENDERERS = {
    "header": _header,
    "nav_bar": _nav_bar,
    "sidebar": _sidebar,
    "form": _form,
    "table": _table,
    "list": _list,
    "card": _card,
    "button": _button,
    "text_block": _text_block,
    "image_placeholder": _image_placeholder,
    "footer": _footer,
}


def _render_component(region, x, y, w):
    fn = _RENDERERS.get(region.get("type", ""))
    if fn is None:
        # Unknown type → render as a text block so nothing is lost
        return _text_block({"content": f"[{region.get('type', 'unknown')}]"}, x, y, w)
    return fn(region, x, y, w)


def _render_screen(screen, ox, oy):
    parts = []
    name = _esc(_clip(screen.get("name", "Screen"), 60))
    purpose = _esc(_clip(screen.get("purpose", ""), 80))
    # Title above the frame
    parts.append(
        f'<text x="{ox}" y="{oy + 22}" font-family="Inter, Arial" font-size="20" font-weight="700" fill="#111827">{name}</text>'
    )
    if purpose:
        parts.append(
            f'<text x="{ox}" y="{oy + 40}" font-family="Inter, Arial" font-size="12" fill="#6b7280">{purpose}</text>'
        )
    # Frame
    fx, fy = ox, oy + TITLE_BAR_H
    parts.append(
        f'<rect x="{fx}" y="{fy}" width="{SCREEN_W}" height="{SCREEN_H}" rx="10" '
        f'fill="white" stroke="#9ca3af" stroke-width="2"/>'
    )
    # Stack components inside the frame
    cy = fy + INNER_PAD
    cx = fx + INNER_PAD
    cw = SCREEN_W - 2 * INNER_PAD
    for region in screen.get("regions", []) or []:
        svg, dh = _render_component(region, cx, cy, cw)
        if cy + dh > fy + SCREEN_H - INNER_PAD:
            break  # don't overflow the frame
        parts.append(svg)
        cy += dh + COMPONENT_GAP
    return "\n".join(parts)


def render_wireframes(schema: dict) -> str:
    screens = schema.get("screens", []) or []
    if not screens:
        # Empty schema → minimal placeholder SVG (still valid for download)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200" viewBox="0 0 600 200">'
            '<rect width="600" height="200" fill="#f7f7f9"/>'
            '<text x="300" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#6b7280">'
            'No screens generated.</text></svg>'
        )

    rows = (len(screens) + SCREENS_PER_ROW - 1) // SCREENS_PER_ROW
    cols = min(len(screens), SCREENS_PER_ROW)
    canvas_w = cols * SCREEN_W + (cols + 1) * GAP_X
    canvas_h = rows * (SCREEN_H + TITLE_BAR_H) + (rows + 1) * GAP_Y

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}">',
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="#f7f7f9"/>',
    ]

    for i, screen in enumerate(screens):
        row = i // SCREENS_PER_ROW
        col = i % SCREENS_PER_ROW
        x = GAP_X + col * (SCREEN_W + GAP_X)
        y = GAP_Y + row * (SCREEN_H + TITLE_BAR_H + GAP_Y)
        parts.append(_render_screen(screen, x, y))

    parts.append("</svg>")
    return "\n".join(parts)
