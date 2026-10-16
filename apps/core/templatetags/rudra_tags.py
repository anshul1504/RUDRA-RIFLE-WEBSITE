import logging
import os
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, number, param="page"):
    """Current URL's query string with `param` set to `number` (other filters are kept)."""
    query = context["request"].GET.copy()
    query[param] = number
    return "?" + query.urlencode()


@register.filter
def simple_markup(text):
    """Render staff-entered plain text: paragraphs, '## ' headings, '- ' bullets. Output is escaped."""
    out, bullets, para = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + "<br>".join(para) + "</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            out.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            flush_para()
            flush_bullets()
        elif line.startswith("## "):
            flush_para()
            flush_bullets()
            out.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("- "):
            flush_para()
            bullets.append(escape(line[2:]))
        else:
            flush_bullets()
            para.append(escape(line))
    flush_para()
    flush_bullets()
    return mark_safe("".join(out))


@register.simple_tag(takes_context=True)
def nav_active(context, *namespaces):
    """Return 'active' when the current URL namespace (or view name) is one of the given names."""
    match = getattr(context.get("request"), "resolver_match", None)
    if not match:
        return ""
    current = {match.view_name, match.namespace}
    return "active" if current & set(namespaces) else ""


_log = logging.getLogger(__name__)


@register.filter
def thumb(image, width=800):
    """URL of a cached, smaller WebP copy of an uploaded image (falls back to the original on any problem).

    Cards and grids show images at 300-700 px, so decoding the full 1800-2000 px upload wastes memory and
    stalls scrolling. Copies are created on first use under MEDIA_ROOT/thumbs/<width>/ and reused afterwards.
    """
    if not image:
        return ""
    try:
        w = int(width)
        src = Path(image.path)
        rel = f"thumbs/{w}/{src.stem}-{int(src.stat().st_mtime)}.webp"
        dest = Path(settings.MEDIA_ROOT) / rel
        if not dest.exists():
            from PIL import Image, ImageOps

            with Image.open(src) as im:
                if im.width <= w:
                    return image.url
                im = ImageOps.exif_transpose(im)
                im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                im.thumbnail((w, int(w * 4)), Image.LANCZOS)
                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_suffix(".tmp")
                im.save(tmp, "WEBP", quality=80, method=4)
                os.replace(tmp, dest)
        return settings.MEDIA_URL + rel
    except Exception:  # noqa: BLE001 - never break a page because a thumbnail failed
        _log.exception("Could not create thumbnail for %s", getattr(image, "name", image))
        return image.url
