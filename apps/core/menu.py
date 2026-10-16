"""Header menu: which items are shown, and how the template renders them."""
from django.urls import reverse

# key, label, url name, is_cta   (also used as the fallback when the table is empty)
DEFAULT_MENU = [
    ("home", "Home", "core:home", False),
    ("about", "About Us", "core:about", False),
    ("programs", "Training Programs", "programs:list", False),
    ("facilities", "Facilities", "core:facilities", False),
    ("gallery", "Gallery", "gallery:index", False),
    ("achievements", "Achievements", "achievements:list", False),
    ("events", "Events", "events:list", False),
    ("contact", "Contact", "contact:contact", False),
    ("enquiry", "Admission Enquiry", "admissions:enquiry", True),
]

# Items whose *page* can also be switched off completely in Site settings (-> 404). Then the link is hidden as well.
PAGE_SWITCH = {"gallery": "show_gallery", "achievements": "show_achievements", "events": "show_events"}


def build_menu(request, site):
    """Return (nav_items, nav_cta, visible) for templates.

    nav_items: ordered dicts for the visible, non-button items; nav_cta: the highlighted button (or None);
    visible: {key: bool} so footer/home sections can follow the same switches.
    """
    from .models import MenuItem

    rows = list(MenuItem.objects.all())
    if not rows:  # never leave the site without a menu
        rows = [MenuItem(key=k, label=l, url_name=u, is_cta=c, order=i, is_visible=True) for i, (k, l, u, c) in enumerate(DEFAULT_MENU)]
    match = getattr(request, "resolver_match", None)
    items, cta, visible = [], None, {}
    for row in rows:
        flag = PAGE_SWITCH.get(row.key)
        shown = row.is_visible and (flag is None or getattr(site, flag))
        visible[row.key] = shown
        if not shown:
            continue
        namespace = row.url_name.split(":")[0]
        if match is None:
            active = False
        elif namespace == "core":
            active = match.view_name == row.url_name
        else:
            active = match.namespace == namespace
        entry = {"key": row.key, "label": row.label, "url": reverse(row.url_name), "active": active}
        if row.is_cta:
            cta = entry
        else:
            items.append(entry)
    return items, cta, visible
