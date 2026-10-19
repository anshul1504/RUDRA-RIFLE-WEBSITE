"""Tests for the seven client change requests (Instagram reels, map, program order, scrolling, footer colour,
booking fields, header menu visibility)."""
import html as htmllib
import re
from datetime import time, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Slot, SlotBooking
from apps.core.models import InstagramReel, MenuItem, SiteSettings
from apps.core.templatetags.rudra_tags import thumb
from apps.core.tests import BaseTest, make_image
from apps.core.validators import validate_instagram_post_url
from apps.programs.models import Program

STATIC = Path(settings.BASE_DIR) / "static"
CSS = (STATIC / "css" / "main.css").read_text(encoding="utf8")
JS = (STATIC / "js" / "main.js").read_text(encoding="utf8")

REEL = "https://www.instagram.com/reel/C1a2B3c4D5e/"


# ------------------------------------------------------------------ Task 1
class InstagramReelTests(BaseTest):
    def test_validator_accepts_specific_reel_links_only(self):
        for ok in [REEL, "https://instagram.com/reel/C1a2B3c4D5e", "https://www.instagram.com/reel/C1a2B3c4D5e/?igsh=abc123",
                   "https://www.instagram.com/p/C1a2B3c4D5e/", "https://www.instagram.com/someuser/reel/C1a2B3c4D5e/"]:
            validate_instagram_post_url(ok)
        for bad in ["https://www.instagram.com/rntpluswelfarefoundation/", "https://www.instagram.com/", "https://www.instagram.com/reels/",
                    "https://evil.example.com/reel/C1a2B3c4D5e/", "https://www.instagram.com.evil.com/reel/C1a2B3c4D5e/", "javascript:alert(1)"]:
            with self.assertRaises(ValidationError, msg=bad):
                validate_instagram_post_url(bad)

    def test_reels_hidden_until_published_and_never_on_homepage(self):
        gallery = reverse("gallery:index")
        self.assertNotContains(self.client.get(gallery), 'id="reels"')
        InstagramReel.objects.create(title="Hidden", url=REEL, thumbnail=make_image("t.jpg"), is_published=False)
        self.assertNotContains(self.client.get(gallery), 'id="reels"')
        InstagramReel.objects.create(title="Shown", url=REEL, thumbnail=make_image("s.jpg"))
        self.assertContains(self.client.get(gallery), 'id="reels"')
        home = self.client.get("/").content.decode()
        self.assertNotIn('id="reels"', home)  # homepage never shows the reel section
        self.assertNotIn("On Instagram", home)

    def test_thumbnail_links_to_exact_reel_in_new_tab(self):
        a = InstagramReel.objects.create(title="Morning drill", url=REEL, thumbnail=make_image("a.jpg"), order=1)
        b = InstagramReel.objects.create(title="Pistol tips", url="https://www.instagram.com/reel/ZZ9y8X7w6V5/", thumbnail=make_image("b.jpg"), order=2)
        for page in (reverse("gallery:index"),):
            html = self.client.get(page).content.decode()
            self.assertIn('id="reels"', html, page)
            for reel in (a, b):
                tile = re.search(r'<a class="reel" href="%s"[^>]*>' % re.escape(reel.url), html)
                self.assertIsNotNone(tile, f"{reel.url} on {page}")
                self.assertIn('target="_blank"', tile.group(0))
                self.assertIn("noopener", tile.group(0))
                self.assertIn(reel.title, tile.group(0))
            self.assertIn(a.thumbnail.url, html)
            self.assertLess(html.index(a.url), html.index(b.url))  # ordering respected

    def test_follow_button_uses_profile_link_only_when_set(self):
        InstagramReel.objects.create(title="R", url=REEL, thumbnail=make_image("r.jpg"))
        s = SiteSettings.load()
        s.instagram_url = "https://www.instagram.com/rntpluswelfarefoundation/"
        s.save()
        self.assertContains(self.client.get(reverse("gallery:index")), "Follow us on Instagram")

    def test_admin_adds_reel_and_rejects_profile_url(self):
        admin = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.client.force_login(admin)
        bad = self.client.post("/admin/core/instagramreel/add/", {"title": "T", "url": "https://www.instagram.com/profile/", "thumbnail": make_image("x.jpg"), "order": 0, "is_published": "on"})
        self.assertEqual(bad.status_code, 200)
        self.assertEqual(InstagramReel.objects.count(), 0)
        ok = self.client.post("/admin/core/instagramreel/add/", {"title": "T", "url": REEL, "thumbnail": make_image("y.jpg"), "order": 0, "is_published": "on"})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(InstagramReel.objects.get().url, REEL)


# ------------------------------------------------------------------ Task 2
class MapTests(BaseTest):
    LINK = "https://www.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en"
    EMBED = "https://maps.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en&output=embed"

    def test_defaults_use_supplied_coordinates(self):
        s = SiteSettings.load()
        self.assertEqual(s.map_link_url, self.LINK)
        self.assertEqual(s.map_embed_url, self.EMBED)
        self.assertEqual(s.directions_url, self.LINK)

    def test_contact_and_home_render_map_and_same_external_link(self):
        for page in ("/contact/", "/"):
            html = htmllib.unescape(self.client.get(page).content.decode())  # attributes are HTML-escaped (&amp;) in the raw markup
            self.assertIn(f'<iframe src="{self.EMBED}"', html, page)
            self.assertIn(f'href="{self.LINK}"', html, page)
        self.assertNotIn("output=embed", self.LINK)  # the navigation link is not used as an iframe src

    def test_structured_data_has_exact_coordinates(self):
        html = self.client.get("/contact/").content.decode()
        self.assertIn('"latitude": 22.7558407', html)
        self.assertIn('"longitude": 75.7659442', html)

    def test_iframe_is_responsive_and_lazy(self):
        self.assertIn("loading=\"lazy\"", self.client.get("/contact/").content.decode())
        self.assertRegex(CSS, r"\.cx-map iframe \{[^}]*width: 100%[^}]*height: 100%")
        self.assertRegex(CSS, r"\.map-frame iframe \{[^}]*width: 100%")


# ------------------------------------------------------------------ Task 3
class ProgramOrderTests(BaseTest):
    EXPECTED = ["Beginner Shooting Program", "Junior Shooter Development Program", "Advanced Competitive Training", "Pay and Play"]

    def test_queryset_order(self):
        self.assertEqual([p.title for p in Program.objects.filter(is_published=True)], self.EXPECTED)

    def test_every_listing_uses_the_order(self):
        for page in ("/programs/", "/", "/about/"):
            r = self.client.get(page)
            titles = [p.title for p in (r.context["programs"])]
            self.assertEqual(titles, self.EXPECTED, page)
        form = self.client.get("/admission/").context["form"]
        self.assertEqual([p.title for p in form.fields["program"].queryset], self.EXPECTED)
        html = self.client.get("/programs/").content.decode()
        positions = [html.index(t) for t in self.EXPECTED]
        self.assertEqual(positions, sorted(positions))

    def test_admin_order_field_controls_the_order(self):
        junior = Program.objects.get(slug="junior-shooter-development-program")
        junior.order = 9
        junior.save()
        self.assertEqual(Program.objects.filter(is_published=True).last().title, junior.title)

    def test_business_data_unchanged(self):
        pnp = Program.objects.get(slug="pay-and-play")
        self.assertTrue(pnp.allow_booking)
        self.assertEqual((pnp.fees, pnp.batch_timings, pnp.age_eligibility, pnp.duration), ("", "", "", ""))
        self.assertEqual(Program.objects.get(slug="beginner-shooting-program").highlights.count(), 5)


# ------------------------------------------------------------------ Task 4
class ScrollPerformanceTests(BaseTest):
    def test_single_passive_throttled_scroll_listener(self):
        lines = [ln for ln in JS.splitlines() if 'addEventListener("scroll"' in ln]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("passive: true", lines[0])
        self.assertIn("requestAnimationFrame", lines[0])

    def test_smooth_scroll_respects_reduced_motion(self):
        self.assertRegex(CSS, r"@media \(prefers-reduced-motion: no-preference\) \{ html \{ scroll-behavior: smooth; \} \}")
        self.assertNotRegex(CSS, r"(?m)^html \{[^}]*scroll-behavior: smooth")
        self.assertIn("prefers-reduced-motion: reduce", CSS)

    def test_only_hero_rings_animate_continuously(self):
        self.assertIn(".hero .target-rings { animation: spinSlow", CSS)
        self.assertNotRegex(CSS, r"(?m)^\.target-rings \{ animation")

    def test_thumbnail_filter_creates_small_cached_copy(self):
        program = Program.objects.get(slug="beginner-shooting-program")
        program.image = make_image("big.jpg", size=(2000, 1200))
        program.save()
        url = thumb(program.image, 900)
        self.assertIn("/thumbs/900/", url)
        path = Path(settings.MEDIA_ROOT) / url.replace(settings.MEDIA_URL, "", 1)
        self.assertTrue(path.exists())
        from PIL import Image

        with Image.open(path) as im:
            self.assertEqual(im.format, "WEBP")
            self.assertLessEqual(im.width, 900)
        self.assertLess(path.stat().st_size, Path(program.image.path).stat().st_size)
        self.assertEqual(thumb(program.image, 900), url)  # cached, same URL
        self.assertIn("/thumbs/900/", self.client.get("/programs/").content.decode())

    def test_thumbnail_filter_falls_back_safely(self):
        self.assertEqual(thumb(None, 800), "")
        program = Program.objects.get(slug="pay-and-play")
        program.image = make_image("small.jpg", size=(300, 200))
        program.save()
        self.assertEqual(thumb(program.image, 900), program.image.url)  # already small: original used


# ------------------------------------------------------------------ Task 5
class FooterColourTests(BaseTest):
    def test_footer_uses_requested_colour_everywhere(self):
        self.assertIn("--footer-bg: #030b17;", CSS)
        self.assertRegex(CSS, r"\.site-footer \{ background: var\(--footer-bg\);")
        bottom = re.search(r"\.footer-bottom \{([^}]*)\}", CSS).group(1)
        self.assertIn("background: transparent", bottom)  # copyright strip shows the footer colour: no gap or second colour
        footer_rules = re.findall(r"\.(?:site-footer|footer-bottom)[^{]*\{([^}]*)\}", CSS)
        values = [d.split(":", 1)[1].strip() for rule in footer_rules for d in rule.split(";")
                  if d.strip().startswith(("background:", "background-color:"))]
        self.assertTrue(values)
        self.assertTrue(all(v in ("transparent", "var(--footer-bg)") for v in values), values)

    def test_copyright_strip_is_inside_the_footer_element(self):
        html = self.client.get("/").content.decode()
        footer = html.split('<footer class="site-footer">')[1].split("</footer>")[0]
        self.assertIn("footer-bottom", footer)


# ------------------------------------------------------------------ Task 6
BOOKING_DATA = {"name": "Rohan Verma", "mobile": "98765 43210", "email": "rohan@example.com", "participants": 1,
                "experience_level": "intermediate", "shooting_type": "10m_air_pistol", "message": "", "consent": "on"}


def open_slot(days=2, capacity=4):
    return Slot.objects.create(date=timezone.localdate() + timedelta(days=days), start_time=time(6), end_time=time(7), capacity=capacity)


class BookingFieldTests(BaseTest):
    def test_form_shows_both_fields_with_exact_options(self):
        slot = open_slot()
        html = self.client.get(reverse("bookings:book", args=[slot.pk])).content.decode()
        for text in ("Previous Shooting Experience", "Type of Shooting",
                     "Beginner — No Previous Experience", "Intermediate — Some Shooting Experience", "Advanced — Experienced Shooter",
                     "10M Air Rifle", "10M Air Pistol"):
            self.assertIn(text, html)
        self.assertEqual(SlotBooking.ShootingType.values, ["10m_air_rifle", "10m_air_pistol"])  # exactly these two

    def test_booking_saves_both_values_and_confirmation_shows_them(self):
        slot = open_slot()
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), BOOKING_DATA)
        b = SlotBooking.objects.get()
        self.assertRedirects(r, reverse("bookings:confirmation", args=[b.reference]), fetch_redirect_response=False)
        self.assertEqual((b.experience_level, b.shooting_type), ("intermediate", "10m_air_pistol"))
        page = self.client.get(reverse("bookings:confirmation", args=[b.reference]))
        self.assertContains(page, "10M Air Pistol")
        self.assertContains(page, "Intermediate — Some Shooting Experience")

    def test_both_fields_are_required_server_side(self):
        slot = open_slot()
        url = reverse("bookings:book", args=[slot.pk])
        for missing in ("experience_level", "shooting_type"):
            data = {k: v for k, v in BOOKING_DATA.items() if k != missing}
            r = self.client.post(url, data)
            self.assertEqual(SlotBooking.objects.count(), 0, missing)
            self.assertIn(missing, r.context["form"].errors)
            self.assertContains(r, "field-error")

    def test_invalid_choices_are_rejected(self):
        slot = open_slot()
        url = reverse("bookings:book", args=[slot.pk])
        for field, bad in (("shooting_type", "25m_rifle"), ("experience_level", "expert"), ("shooting_type", "10M Air Rifle")):
            r = self.client.post(url, {**BOOKING_DATA, field: bad})
            self.assertEqual(SlotBooking.objects.count(), 0, (field, bad))
            self.assertIn(field, r.context["form"].errors)

    def test_existing_bookings_are_preserved(self):
        slot = open_slot()
        old = SlotBooking.objects.create(slot=slot, name="Old", mobile="9876543210", consent=True)  # made before the fields existed
        old.refresh_from_db()
        self.assertEqual((old.experience_level, old.shooting_type), ("", ""))
        old.full_clean()  # still valid, never forced to have a value

    def test_admin_displays_values_filters_and_exports_labels(self):
        slot = open_slot()
        self.client.post(reverse("bookings:book", args=[slot.pk]), BOOKING_DATA)
        b = SlotBooking.objects.get()
        admin = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.client.force_login(admin)
        lst = self.client.get("/admin/bookings/slotbooking/")
        self.assertContains(lst, "10M Air Pistol")
        self.assertContains(lst, "Intermediate — Some Shooting Experience")
        detail = self.client.get(f"/admin/bookings/slotbooking/{b.pk}/change/")
        self.assertContains(detail, "10M Air Pistol")
        self.assertContains(detail, "Previous shooting experience")
        self.assertEqual(self.client.get("/admin/bookings/slotbooking/?shooting_type__exact=10m_air_pistol").context["cl"].result_count, 1)
        self.assertEqual(self.client.get("/admin/bookings/slotbooking/?shooting_type__exact=10m_air_rifle").context["cl"].result_count, 0)
        csv = self.client.post("/admin/bookings/slotbooking/", {"action": "export_csv", "_selected_action": [b.pk]}).content.decode("utf-8")
        self.assertIn("10M Air Pistol", csv)
        self.assertIn("Intermediate — Some Shooting Experience", csv)
        self.assertNotIn("10m_air_pistol", csv)

    def test_capacity_and_duplicate_rules_still_apply(self):
        slot = open_slot(capacity=1)
        self.client.post(reverse("bookings:book", args=[slot.pk]), BOOKING_DATA)
        from django.core.cache import cache

        cache.clear()
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), {**BOOKING_DATA, "mobile": "9123456780"})
        self.assertEqual(SlotBooking.objects.count(), 1)
        self.assertContains(r, "now full")


# ------------------------------------------------------------------ Task 7
class HeaderMenuTests(BaseTest):
    ALL = ["home", "about", "programs", "facilities", "gallery", "achievements", "events", "contact", "enquiry"]

    def header(self, page="/about/"):
        return self.client.get(page).content.decode().split("</header>")[0]

    def test_nine_items_seeded_with_only_achievements_hidden(self):
        self.assertEqual(list(MenuItem.objects.values_list("key", flat=True)), self.ALL)
        self.assertEqual(list(MenuItem.objects.filter(is_visible=False).values_list("key", flat=True)), ["achievements"])

    def test_achievements_hidden_everywhere_in_navigation_but_page_still_works(self):
        header = self.header()
        self.assertNotIn(">Achievements<", header)
        for label in ("Home", "About Us", "Training Programs", "Facilities", "Gallery", "Events", "Contact", "Admission Enquiry"):
            self.assertIn(f">{label}<", header)
        html = self.client.get("/").content.decode()
        footer = html.split('<footer class="site-footer">')[1]
        self.assertNotIn("Achievements", footer)
        self.assertNotIn("What we work toward", html)  # homepage section follows the switch
        self.assertEqual(self.client.get("/achievements/").status_code, 200)  # route and content untouched

    def test_enabling_achievements_restores_it_without_recreating_content(self):
        from apps.achievements.models import Achievement

        Achievement.objects.create(title="Verified Result", is_published=True)
        MenuItem.objects.filter(key="achievements").update(is_visible=True)
        self.assertIn(">Achievements<", self.header())
        self.assertIn("What we work toward", self.client.get("/").content.decode())
        self.assertContains(self.client.get("/achievements/"), "Verified Result")  # same content, nothing recreated

    def test_every_item_can_be_hidden_and_is_independent(self):
        for key in ["home", "about", "programs", "facilities", "gallery", "events", "contact", "enquiry"]:
            MenuItem.objects.update(is_visible=True)
            MenuItem.objects.filter(key=key).update(is_visible=False)
            label = MenuItem.objects.get(key=key).label
            header = self.header("/programs/")
            self.assertNotIn(f">{label}<", header, key)
            others = [m.label for m in MenuItem.objects.exclude(key__in=[key, "achievements"])]
            for other in others:
                self.assertIn(f">{other}<", header, (key, other))

    def test_hidden_item_pages_stay_reachable(self):
        MenuItem.objects.update(is_visible=False)
        for url in ("/about/", "/programs/", "/facilities/", "/gallery/", "/events/", "/contact/", "/admission/", "/achievements/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        header = self.header("/about/")
        self.assertNotIn('class="nav-link', header)

    def test_page_switch_and_menu_switch_both_apply(self):
        MenuItem.objects.filter(key="gallery").update(is_visible=True)
        s = SiteSettings.load()
        s.show_gallery = False
        s.save()
        self.assertNotIn(">Gallery<", self.header())
        self.assertEqual(self.client.get("/gallery/").status_code, 404)  # page switch (separate control) still 404s

    def test_active_link_highlighting(self):
        self.assertRegex(self.header("/programs/"), r'nav-link active" href="/programs/" aria-current="page"')
        self.assertRegex(self.header("/about/"), r'nav-link active" href="/about/"')

    def test_menu_falls_back_to_defaults_if_table_empty(self):
        MenuItem.objects.all().delete()
        header = self.header()
        self.assertIn(">Home<", header)
        self.assertIn(">Achievements<", header)

    def test_mobile_and_desktop_share_the_same_markup(self):
        header = self.header()
        self.assertEqual(header.count('id="mainNav"'), 1)  # one list serves the collapsed (mobile) and expanded menu
        self.assertNotIn(">Achievements<", header)


class HeaderMenuAdminTests(BaseTest):
    def setUp(self):
        super().setUp()
        call_command("create_staff_groups", verbosity=0)
        self.root = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.editor = User.objects.create_user("editor", password="pass-12345-xyz", is_staff=True)
        self.editor.groups.add(Group.objects.get(name="Content Editors"))

    def test_superuser_toggles_visibility_in_admin_and_it_persists(self):
        item = MenuItem.objects.get(key="achievements")
        self.client.force_login(self.root)
        page = self.client.get("/admin/core/menuitem/")
        self.assertContains(page, "Achievements")
        self.assertContains(page, "/achievements/")
        r = self.client.post(f"/admin/core/menuitem/{item.pk}/change/", {"is_visible": "on"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(MenuItem.objects.get(key="achievements").is_visible)
        fresh = Client()  # a visitor with a brand-new session, i.e. after reload / logout / login / restart
        self.assertIn(">Achievements<", fresh.get("/about/").content.decode().split("</header>")[0])
        self.client.post(f"/admin/core/menuitem/{item.pk}/change/", {})  # unticked
        self.assertFalse(MenuItem.objects.get(key="achievements").is_visible)
        self.assertNotIn(">Achievements<", Client().get("/about/").content.decode().split("</header>")[0])

    def test_inline_list_toggle_for_all_items(self):
        self.client.force_login(self.root)
        items = list(MenuItem.objects.order_by("order"))
        data = {"form-TOTAL_FORMS": len(items), "form-INITIAL_FORMS": len(items), "form-MIN_NUM_FORMS": 0, "form-MAX_NUM_FORMS": 1000, "_save": "Save"}
        for i, m in enumerate(items):
            data[f"form-{i}-id"] = m.pk
            if m.key not in ("contact", "gallery"):
                data[f"form-{i}-is_visible"] = "on"
        r = self.client.post("/admin/core/menuitem/", data)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(sorted(MenuItem.objects.filter(is_visible=False).values_list("key", flat=True)), ["contact", "gallery"])

    def test_items_cannot_be_added_or_deleted(self):
        self.client.force_login(self.root)
        item = MenuItem.objects.first()
        self.assertEqual(self.client.get("/admin/core/menuitem/add/").status_code, 403)
        self.assertEqual(self.client.get(f"/admin/core/menuitem/{item.pk}/delete/").status_code, 403)

    def test_only_authorised_users_can_change_visibility(self):
        item = MenuItem.objects.get(key="achievements")
        self.assertEqual(self.client.get("/admin/core/menuitem/").status_code, 302)  # anonymous -> login
        self.client.post(f"/admin/core/menuitem/{item.pk}/change/", {"is_visible": "on"})
        self.assertFalse(MenuItem.objects.get(key="achievements").is_visible)
        outsider = User.objects.create_user("outsider", password="pass-12345-xyz", is_staff=True)  # staff but no permission
        self.client.force_login(outsider)
        self.assertEqual(self.client.get("/admin/core/menuitem/").status_code, 403)
        self.assertEqual(self.client.post(f"/admin/core/menuitem/{item.pk}/change/", {"is_visible": "on"}).status_code, 403)
        self.assertFalse(MenuItem.objects.get(key="achievements").is_visible)
        self.client.force_login(self.editor)  # content editors are not given this control by default
        self.assertEqual(self.client.get("/admin/core/menuitem/").status_code, 403)


# ------------------------------------------------------------------ small-screen header + program photo focus
class MobileHeaderAndPhotoFocusTests(BaseTest):
    def test_admission_button_sits_beside_the_hamburger_on_small_screens(self):
        header = self.client.get("/about/").content.decode().split("</header>")[0]
        toggler = header.index('class="navbar-toggler"')
        mobile_cta = header.index("nav-cta-mobile")
        self.assertLess(mobile_cta, toggler)  # button comes right before the hamburger, outside the collapsed menu
        self.assertLess(mobile_cta, header.index('id="mainNav"'))
        self.assertIn("d-xl-none", header[mobile_cta - 80:mobile_cta + 120])  # only shown below the desktop breakpoint
        self.assertIn('nav-cta ms-xl-3 d-none d-xl-block', header)  # desktop copy lives inside the menu

    def test_mobile_admission_button_follows_menu_switch(self):
        MenuItem.objects.filter(key="enquiry").update(is_visible=False)
        self.assertNotIn("nav-cta-mobile", self.client.get("/about/").content.decode())

    def test_pay_and_play_photo_is_anchored_to_the_top(self):
        pnp = Program.objects.get(slug="pay-and-play")
        self.assertEqual(pnp.image_focus, "top")
        self.assertEqual(pnp.focus_css, "50% 0%")
        pnp.image = make_image("pnp.jpg", size=(720, 1280))
        pnp.save()
        self.assertContains(self.client.get("/programs/"), 'style="object-position: 50% 0%"')
        self.assertContains(self.client.get(pnp.get_absolute_url()), 'style="object-position: 50% 0%"')
        beginner = Program.objects.get(slug="beginner-shooting-program")
        self.assertEqual(beginner.focus_css, "50% 50%")  # other programs unchanged


class StaticStorageTests(BaseTest):
    def test_manifest_storage_tolerates_directory_references(self):
        from config.storage import RelaxedManifestStorage

        self.assertFalse(RelaxedManifestStorage.manifest_strict)  # jazzmin asks for {% static 'vendor/bootswatch' %}


class GalleryVideoTests(BaseTest):
    def test_videos_section_only_when_published(self):
        from django.core.files.base import ContentFile

        from apps.gallery.models import GalleryVideo

        url = reverse("gallery:index")
        self.assertNotContains(self.client.get(url), "videos-title")
        v = GalleryVideo(title="Range clip")
        v.video.save("clip.mp4", ContentFile(b"\x00\x00\x00\x18ftypmp42"), save=False)
        v.save()
        self.assertContains(self.client.get(url), "videos-title")
        v.is_published = False
        v.save()
        self.assertNotContains(self.client.get(url), "videos-title")
        v.video.delete(save=False)

    def test_video_validator_rejects_wrong_type(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.core.validators import validate_video_upload

        with self.assertRaises(ValidationError):
            validate_video_upload(SimpleUploadedFile("x.exe", b"abc"))
        validate_video_upload(SimpleUploadedFile("x.mp4", b"abc"))


class LaunchCountdownTests(BaseTest):
    def set_launch(self, minutes, enabled=True):
        s = SiteSettings.load()
        s.launch_countdown_enabled = enabled
        s.launch_at = timezone.now() + timedelta(minutes=minutes)
        s.save()

    def test_countdown_shown_before_launch_time(self):
        self.set_launch(30)
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, 'role="timer"')
        self.assertNotContains(r, "Admission Enquiry")
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        self.assertContains(self.client.get(reverse("contact:contact")), 'role="timer"')

    def test_site_opens_after_launch_time_or_when_switched_off(self):
        self.set_launch(-1)
        self.assertNotContains(self.client.get(reverse("core:home")), 'role="timer"')
        self.set_launch(30, enabled=False)
        self.assertNotContains(self.client.get(reverse("core:home")), 'role="timer"')

    def test_admin_static_and_staff_preview_stay_open(self):
        self.set_launch(30)
        self.assertNotContains(self.client.get("/admin/login/"), 'role="timer"')
        staff = User.objects.create_user("preview", password="x", is_staff=True)
        self.client.force_login(staff)
        self.assertNotContains(self.client.get(reverse("core:home")), 'role="timer"')

    def test_status_endpoint_follows_admin_changes(self):
        self.set_launch(30)
        first = self.client.get("/launch-status/").json()["remaining"]
        self.assertTrue(1700 < first <= 1800)
        self.set_launch(60)
        self.assertTrue(self.client.get("/launch-status/").json()["remaining"] > 3500)
        self.set_launch(30, enabled=False)
        self.assertEqual(self.client.get("/launch-status/").json()["remaining"], 0)


class LaunchStaffNoticeTests(LaunchCountdownTests):
    def test_staff_sees_notice_and_can_preview_visitor_view(self):
        self.set_launch(30)
        staff = User.objects.create_user("preview2", password="x", is_staff=True)
        self.client.force_login(staff)
        home = self.client.get(reverse("core:home"))
        self.assertContains(home, "Countdown is running for visitors")
        self.assertContains(self.client.get("/?preview=countdown"), 'role="timer"')
