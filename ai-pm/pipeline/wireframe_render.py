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


def _hotspot(fragment: str, to) -> str:
    """Wrap an SVG fragment so it becomes a clickable navigation target in the
    interactive prototype. `data-to` carries the destination screen id; the
    prototype HTML shell binds the click. In a downloaded static .svg this is
    inert (no JS), so the same renderers serve both outputs."""
    if not to:
        return fragment
    return (f'<g class="pm-hotspot" data-to="{_esc(to)}" style="cursor:pointer">'
            f'{fragment}</g>')


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
    links = r.get("links", {}) or {}
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f3f4f6" stroke="#e5e7eb"/>']
    cx = x + 16
    for item in items[:8]:
        label = _clip(item, 18)
        is_active = item == active
        text_w = max(60, 9 * len(label) + 24)
        item_parts = []
        if is_active:
            item_parts.append(
                f'<rect x="{cx}" y="{y + 8}" width="{text_w}" height="{h - 16}" rx="14" fill="#1f2937"/>'
            )
            item_parts.append(
                f'<text x="{cx + text_w / 2}" y="{y + 28}" text-anchor="middle" '
                f'font-family="Inter, Arial" font-size="13" fill="white">{_esc(label)}</text>'
            )
        else:
            item_parts.append(
                f'<text x="{cx + 12}" y="{y + 28}" font-family="Inter, Arial" font-size="13" fill="#4b5563">{_esc(label)}</text>'
            )
        parts.append(_hotspot("\n".join(item_parts), links.get(item)))
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
    submit_frag = (
        f'<rect x="{btn_x}" y="{cy}" width="{btn_w}" height="{submit_h - 8}" rx="6" fill="#2563eb"/>'
        f'<text x="{btn_x + btn_w / 2}" y="{cy + 24}" text-anchor="middle" '
        f'font-family="Inter, Arial" font-size="13" font-weight="600" fill="white">{btn_label}</text>'
    )
    parts.append(_hotspot(submit_frag, r.get("to")))
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
    links = r.get("links", {}) or {}
    item_h = 36
    h = max(item_h * min(len(items), 8) + 8, item_h)
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#e5e7eb"/>']
    for i, item in enumerate(items[:8]):
        cy = y + 6 + i * item_h
        target = links.get(item)
        row_parts = [
            f'<circle cx="{x + 18}" cy="{cy + 16}" r="3" fill="#6b7280"/>',
            f'<text x="{x + 32}" y="{cy + 22}" font-family="Inter, Arial" font-size="13" fill="#374151">{_esc(_clip(item, 80))}</text>',
        ]
        if target:
            # Transparent overlay so the whole row is clickable, not just the text.
            row_parts.insert(
                0, f'<rect x="{x}" y="{cy}" width="{w}" height="{item_h}" fill="transparent"/>'
            )
        parts.append(_hotspot("\n".join(row_parts), target))
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
        action_frag = (
            f'<rect x="{btn_x}" y="{y + h - 38}" width="{btn_w}" height="28" rx="4" fill="#1f2937"/>'
            f'<text x="{btn_x + btn_w / 2}" y="{y + h - 19}" text-anchor="middle" '
            f'font-family="Inter, Arial" font-size="12" fill="white">{action}</text>'
        )
        parts.append(_hotspot(action_frag, r.get("to")))
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
    return _hotspot("\n".join(parts), r.get("to")), h


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


# ── Interactive click-through prototype ──────────────────────────────────────────
# One screen visible at a time on a device frame; clicking a wired element (button,
# card action, nav item, list row carrying a `to`/`links` target) navigates to the
# destination screen — entirely client-side, so it runs inside Streamlit's iframe
# and as a standalone downloadable .html.

def _screen_svg(screen) -> str:
    """A single screen rendered as a standalone, responsive SVG (origin 0,0)."""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SCREEN_W} {SCREEN_H}" '
        f'preserveAspectRatio="xMidYMin meet" '
        f'style="display:block;width:100%;height:auto">',
        f'<rect x="0" y="0" width="{SCREEN_W}" height="{SCREEN_H}" fill="white"/>',
    ]
    cy = INNER_PAD
    cx = INNER_PAD
    cw = SCREEN_W - 2 * INNER_PAD
    for region in screen.get("regions", []) or []:
        svg, dh = _render_component(region, cx, cy, cw)
        if cy + dh > SCREEN_H - INNER_PAD:
            break  # don't overflow the frame
        parts.append(svg)
        cy += dh + COMPONENT_GAP
    parts.append("</svg>")
    return "\n".join(parts)


def render_prototype_html(schema: dict) -> str:
    """Self-contained interactive prototype: device frame, clickable hotspots,
    a thumbnail filmstrip, and Back/Prev/Next controls. Works embedded in
    Streamlit and as a standalone downloaded file."""
    screens = schema.get("screens", []) or []
    if not screens:
        return (
            '<!doctype html><html><body style="font-family:Inter,Arial;padding:40px;'
            'color:#6b7280">No screens generated.</body></html>'
        )

    # Build the deck (one positioned screen container per screen) and the filmstrip.
    deck, strip = [], []
    ids = []
    for i, screen in enumerate(screens):
        sid = str(screen.get("id") or f"S{i + 1}")
        ids.append(sid)
        name = _esc(_clip(screen.get("name", f"Screen {i + 1}"), 60))
        purpose = _esc(_clip(screen.get("purpose", ""), 90))
        deck.append(
            f'<div class="pm-screen" data-id="{sid}" data-index="{i}" '
            f'data-name="{name}" style="display:none">'
            f'{_screen_svg(screen)}</div>'
        )
        strip.append(
            f'<button class="pm-thumb" data-index="{i}" title="{purpose}">'
            f'<span class="pm-thumb-n">{i + 1}</span> {name}</button>'
        )

    ids_json = "[" + ",".join(f'"{_esc(s)}"' for s in ids) + "]"

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Inter, -apple-system, Arial, sans-serif;
         background: #f1f5f9; color: #111827; }}
  .pm-wrap {{ display: flex; flex-direction: column; height: 100vh; }}
  .pm-topbar {{ display: flex; align-items: center; gap: 10px; padding: 10px 14px;
               background: #fff; border-bottom: 1px solid #e5e7eb; flex: 0 0 auto; }}
  .pm-topbar .pm-title {{ font-weight: 700; font-size: 15px; }}
  .pm-topbar .pm-step {{ color: #6b7280; font-size: 13px; }}
  .pm-spacer {{ flex: 1; }}
  .pm-btn {{ border: 1px solid #d1d5db; background: #fff; border-radius: 6px;
            padding: 6px 12px; font-size: 13px; cursor: pointer; }}
  .pm-btn:hover {{ background: #f3f4f6; }}
  .pm-btn:disabled {{ opacity: .4; cursor: default; }}
  .pm-body {{ display: flex; flex: 1; min-height: 0; }}
  .pm-strip {{ flex: 0 0 200px; overflow-y: auto; background: #fff;
              border-right: 1px solid #e5e7eb; padding: 8px; }}
  .pm-thumb {{ display: block; width: 100%; text-align: left; border: 1px solid #e5e7eb;
              background: #fff; border-radius: 6px; padding: 8px 10px; margin-bottom: 6px;
              font-size: 12px; cursor: pointer; color: #374151; }}
  .pm-thumb:hover {{ background: #f3f4f6; }}
  .pm-thumb.active {{ border-color: #2563eb; background: #eff6ff; color: #1d4ed8; font-weight: 600; }}
  .pm-thumb-n {{ display: inline-block; min-width: 18px; height: 18px; line-height: 18px;
                text-align: center; background: #e5e7eb; color: #374151; border-radius: 9px;
                font-size: 11px; margin-right: 6px; }}
  .pm-stage {{ flex: 1; overflow: auto; padding: 24px; }}
  .pm-stage-inner {{ width: 100%; max-width: 1180px; margin: 0 auto; }}
  .pm-frame {{ width: 100%; background: #fff; border: 1px solid #cbd5e1;
              border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.08); overflow: hidden; }}
  .pm-hint {{ text-align: center; color: #94a3b8; font-size: 12px; padding-top: 10px; }}
  .pm-hotspot:hover {{ outline: 2px solid #2563eb; outline-offset: 1px; }}
</style></head>
<body>
<div class="pm-wrap">
  <div class="pm-topbar">
    <span class="pm-title" id="pm-name"></span>
    <span class="pm-step" id="pm-step"></span>
    <span class="pm-spacer"></span>
    <button class="pm-btn" id="pm-back">↩ Back</button>
    <button class="pm-btn" id="pm-prev">‹ Prev</button>
    <button class="pm-btn" id="pm-next">Next ›</button>
  </div>
  <div class="pm-body">
    <div class="pm-strip">{''.join(strip)}</div>
    <div class="pm-stage">
      <div class="pm-stage-inner">
        <div class="pm-frame" id="pm-frame">{''.join(deck)}</div>
        <div class="pm-hint">Click a button, tab, or list row to navigate. Use the
          list on the left or Prev/Next to move between screens.</div>
      </div>
    </div>
  </div>
</div>
<script>
  var IDS = {ids_json};
  var screens = Array.prototype.slice.call(document.querySelectorAll('.pm-screen'));
  var thumbs = Array.prototype.slice.call(document.querySelectorAll('.pm-thumb'));
  var navStack = [];
  var cur = 0;

  function show(idx, record) {{
    if (idx < 0 || idx >= screens.length) return;
    if (record && idx !== cur) navStack.push(cur);
    cur = idx;
    screens.forEach(function (s, i) {{ s.style.display = (i === idx) ? 'block' : 'none'; }});
    thumbs.forEach(function (t, i) {{ t.classList.toggle('active', i === idx); }});
    document.getElementById('pm-name').textContent = screens[idx].getAttribute('data-name');
    document.getElementById('pm-step').textContent = '(' + (idx + 1) + ' / ' + screens.length + ')';
    document.getElementById('pm-prev').disabled = (idx === 0);
    document.getElementById('pm-next').disabled = (idx === screens.length - 1);
    document.getElementById('pm-back').disabled = (navStack.length === 0);
  }}

  function gotoId(id) {{
    var i = IDS.indexOf(id);
    if (i >= 0) show(i, true);
  }}

  document.getElementById('pm-frame').addEventListener('click', function (e) {{
    var hs = e.target.closest('.pm-hotspot');
    if (hs) gotoId(hs.getAttribute('data-to'));
  }});
  thumbs.forEach(function (t) {{
    t.addEventListener('click', function () {{ show(parseInt(t.getAttribute('data-index'), 10), true); }});
  }});
  document.getElementById('pm-prev').addEventListener('click', function () {{ show(cur - 1, true); }});
  document.getElementById('pm-next').addEventListener('click', function () {{ show(cur + 1, true); }});
  document.getElementById('pm-back').addEventListener('click', function () {{
    if (navStack.length) show(navStack.pop(), false);
  }});

  show(0, false);
</script>
</body></html>"""
