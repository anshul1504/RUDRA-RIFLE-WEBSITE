import io
import re
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.achievements.models import Achievement
from apps.admissions.forms import AdmissionEnquiryForm, normalise_mobile
from apps.admissions.models import AdmissionEnquiry
from apps.contact.models import ContactMessage
from apps.events.models import Event
from apps.gallery.models import Category, GalleryImage
from apps.programs.models import Program

from .models import LegalPage, SiteSettings
from .templatetags.rudra_tags import simple_markup
from .validators import validate_image_upload

MEDIA = tempfile.mkdtemp()


def make_image(name="photo.jpg", fmt="JPEG", size=(300, 200)):
    buf = io.BytesIO()
    Image.new("RGB", size, (64, 54, 117)).save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=MEDIA)
class BaseTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()


class PublicPagesTests(BaseTest):
    def test_all_public_routes_load(self):
        names = [
            "core:home", "core:about", "programs:list", "core:facilities", "gallery:index",
            "achievements:list", "events:list", "admissions:enquiry", "contact:contact",
            "core:privacy", "core:terms", "bookings:slots",
        ]
        for name in names:
            with self.subTest(name=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, "<title>")
                self.assertContains(r, 'rel="canonical"')
                self.assertContains(r, "rudra-logo.svg")

    def test_seeded_programs_and_facilities(self):
        self.assertEqual(Program.objects.count(), 4)
        r = self.client.get(reverse("programs:list"))
        self.assertContains(r, "Beginner Shooting Program")
        self.assertContains(self.client.get("/programs/beginner-shooting-program/"), "Breathing techniques")
        self.assertContains(r, "Junior Shooter Development Program")
        r = self.client.get(reverse("core:facilities"))
        self.assertContains(r, "Modern Shooting Range")
        self.assertContains(r, "Individual Attention for Every Shooter")

    def test_program_detail_and_unpublished_hidden(self):
        p = Program.objects.get(slug="beginner-shooting-program")
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 200)
        p.is_published = False
        p.save()
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 404)

    def test_program_optional_details_hidden_until_supplied(self):
        p = Program.objects.get(slug="beginner-shooting-program")
        r = self.client.get(p.get_absolute_url())
        self.assertNotContains(r, "Batch timings")
        self.assertNotContains(r, "Fees</span>")
        p.fees = "Rs. 1,000 per month"
        p.save()
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "Rs. 1,000 per month")

    def test_empty_states(self):
        self.assertContains(self.client.get(reverse("gallery:index")), "Photos coming soon")
        self.assertContains(self.client.get(reverse("events:list")), "No upcoming events at the moment")
        self.assertContains(self.client.get(reverse("achievements:list")), "Achievement records will be added here")

    def test_404_uses_custom_template(self):
        r = self.client.get("/definitely-missing/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "We could not find that page", status_code=404)

    def test_robots_and_sitemap(self):
        r = self.client.get("/robots.txt")
        self.assertContains(r, "Disallow: /admin/")
        self.assertContains(r, "sitemap.xml")
        r = self.client.get("/sitemap.xml")
        self.assertContains(r, "/programs/beginner-shooting-program/")

    def test_contact_details_come_from_settings(self):
        r = self.client.get(reverse("contact:contact"))
        self.assertContains(r, "tel:+919425093128")
        self.assertContains(r, "mailto:info@rudrasports.com")
        for other in ("support@", "contact@rudrasports", "help@", "gmail.com"):
            self.assertNotContains(r, other)
        self.assertContains(r, "https://wa.me/919425093128")
        self.assertContains(r, "Pitra Parvat")
        # No invented social links or hours
        self.assertNotContains(r, "facebook.com")
        self.assertNotContains(r, "bi-clock")

    def test_social_links_only_when_set(self):
        s = SiteSettings.load()
        self.assertEqual(s.social_links, [])
        s.instagram_url = "https://instagram.com/example"
        s.save()
        self.assertContains(self.client.get("/"), "https://instagram.com/example")

    def test_site_settings_singleton(self):
        SiteSettings.load()
        SiteSettings(organisation_name="X").save()
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_legal_draft_banner(self):
        r = self.client.get(reverse("core:privacy"))
        self.assertContains(r, "has not yet been reviewed")
        self.assertEqual(self.client.get("/legal/missing/").status_code, 404)

    def test_simple_markup_escapes_html(self):
        out = simple_markup("## Head\n<script>alert(1)</script>\n\n- a\n- b")
        self.assertNotIn("<script>", out)
        self.assertIn("<h2>Head</h2>", out)
        self.assertIn("<li>a</li>", out)


class ContentModelTests(BaseTest):
    def test_slug_generation_unique(self):
        a = Program.objects.create(title="New Program", summary="s")
        b = Program.objects.create(title="New Program", summary="s")
        self.assertEqual(a.slug, "new-program")
        self.assertEqual(b.slug, "new-program-2")

    def test_gallery_filters_and_unpublished(self):
        cat = Category.objects.get(slug="training")
        GalleryImage.objects.create(title="One", image=make_image(), alt_text="Alt one", category=cat)
        GalleryImage.objects.create(title="Hidden", image=make_image("h.jpg"), alt_text="x", category=cat, is_published=False)
        r = self.client.get(reverse("gallery:index"))
        self.assertContains(r, "Alt one")
        self.assertNotContains(r, "Hidden")
        self.assertContains(r, 'data-category="training"')
        self.assertContains(r, 'loading="lazy"')

    def test_large_image_is_downscaled(self):
        cat = Category.objects.first()
        g = GalleryImage.objects.create(title="Big", image=make_image("big.jpg", size=(3000, 2000)), alt_text="a", category=cat)
        with Image.open(g.image.path) as im:
            self.assertLessEqual(max(im.size), 2000)

    def test_events_upcoming_and_past(self):
        now = timezone.now()
        Event.objects.create(title="Future Cup", start_at=now + timedelta(days=10), location="Indore")
        Event.objects.create(title="Old Cup", start_at=now - timedelta(days=30))
        Event.objects.create(title="Draft Cup", start_at=now + timedelta(days=5), is_published=False)
        r = self.client.get(reverse("events:list"))
        self.assertEqual([e.title for e in r.context["upcoming_page"]], ["Future Cup"])
        self.assertEqual([e.title for e in r.context["past_page"]], ["Old Cup"])
        self.assertNotContains(r, "Draft Cup")
        detail = self.client.get(Event.objects.get(title="Future Cup").get_absolute_url())
        self.assertContains(detail, "application/ld+json")
        self.assertEqual(self.client.get(Event.objects.get(title="Draft Cup").get_absolute_url()).status_code, 404)

    def test_event_end_before_start_invalid(self):
        now = timezone.now()
        e = Event(title="Bad", start_at=now, end_at=now - timedelta(hours=1))
        with self.assertRaises(ValidationError):
            e.full_clean()

    def test_achievements_publish_flag(self):
        Achievement.objects.create(title="Verified Result", summary="Real", is_published=True)
        Achievement.objects.create(title="Unverified", is_published=False)
        r = self.client.get(reverse("achievements:list"))
        self.assertContains(r, "Verified Result")
        self.assertNotContains(r, "Unverified")


class UploadValidationTests(BaseTest):
    def test_rejects_non_image_content(self):
        bad = SimpleUploadedFile("evil.jpg", b"<?php echo 1; ?>", content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            validate_image_upload(bad)

    def test_rejects_bad_extension(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(make_image("x.gif"))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_rejects_oversize(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(make_image(size=(500, 500)))

    def test_accepts_valid(self):
        validate_image_upload(make_image())


VALID = {
    "applicant_name": "Aarav Sharma",
    "date_of_birth": "1995-04-12",  # adult: guardian details not needed
    "gender": "male",
    "city": "Indore",
    "institution": "",
    "guardian_name": "",
    "guardian_mobile": "",
    "email": "Aarav@Example.com",
    "mobile": "+91 98765-43210",
    "preferred_contact": "phone",
    "program": "",
    "shooting_interest": "10m_air_rifle",
    "experience_level": "beginner",
    "preferred_time": "",
    "how_heard": "",
    "message": "I would like to join <b>beginner</b> batch.",
    "consent": "on",
}


class AdmissionTests(BaseTest):
    def test_normalise_mobile(self):
        self.assertEqual(normalise_mobile("94250 93128"), "9425093128")
        self.assertEqual(normalise_mobile("+91 94250-93128"), "9425093128")
        self.assertEqual(normalise_mobile("094250 93128"), "9425093128")

    def test_valid_submission_saves_and_redirects(self):
        r = self.client.post(reverse("admissions:enquiry"), VALID)
        self.assertRedirects(r, reverse("admissions:thanks"), fetch_redirect_response=False)
        e = AdmissionEnquiry.objects.get()
        self.assertEqual(e.mobile, "9876543210")
        self.assertEqual(e.email, "aarav@example.com")
        self.assertEqual(e.status, "new")
        self.assertNotIn("<b>", e.message)
        self.assertIsNotNone(e.consent_at)
        self.assertContains(self.client.get(reverse("admissions:thanks")), "Dhanyavad")

    def test_thanks_requires_submission(self):
        self.assertRedirects(self.client.get(reverse("admissions:thanks")), reverse("admissions:enquiry"))

    def test_required_fields_and_consent(self):
        r = self.client.post(reverse("admissions:enquiry"), {})
        self.assertEqual(r.status_code, 200)
        form = r.context["form"]
        for f in ["applicant_name", "email", "mobile", "consent"]:
            self.assertIn(f, form.errors)
        self.assertEqual(AdmissionEnquiry.objects.count(), 0)
        self.assertContains(r, "Please tick the consent box")

    def test_invalid_mobile_and_email(self):
        form = AdmissionEnquiryForm({**VALID, "mobile": "12345", "email": "nope"})
        self.assertFalse(form.is_valid())
        self.assertIn("mobile", form.errors)
        self.assertIn("email", form.errors)

    def test_minor_requires_guardian(self):
        dob = (timezone.localdate() - timedelta(days=365 * 12)).isoformat()
        form = AdmissionEnquiryForm({**VALID, "date_of_birth": dob})
        self.assertFalse(form.is_valid())
        self.assertIn("guardian_name", form.errors)
        self.assertIn("guardian_mobile", form.errors)
        form = AdmissionEnquiryForm({**VALID, "date_of_birth": dob, "guardian_name": "Parent"})
        self.assertFalse(form.is_valid())  # guardian mobile still missing
        self.assertEqual(list(form.errors), ["guardian_mobile"])
        form = AdmissionEnquiryForm({**VALID, "date_of_birth": dob, "guardian_name": "Parent", "guardian_mobile": "+91 98765 11111"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["guardian_mobile"], "9876511111")

    def test_future_dob_rejected(self):
        dob = (timezone.localdate() + timedelta(days=5)).isoformat()
        self.assertIn("date_of_birth", AdmissionEnquiryForm({**VALID, "date_of_birth": dob}).errors)

    def test_duplicate_submission_blocked(self):
        self.client.post(reverse("admissions:enquiry"), VALID)
        r = self.client.post(reverse("admissions:enquiry"), VALID)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(AdmissionEnquiry.objects.count(), 1)
        self.assertContains(r, "already received")

    def test_honeypot_blocks_bots(self):
        r = self.client.post(reverse("admissions:enquiry"), {**VALID, "contact_website": "http://spam"})
        self.assertEqual(AdmissionEnquiry.objects.count(), 0)
        self.assertEqual(r.status_code, 200)

    def test_csrf_enforced(self):
        from django.test import Client

        c = Client(enforce_csrf_checks=True)
        self.assertEqual(c.post(reverse("admissions:enquiry"), VALID).status_code, 403)

    def test_throttle(self):
        for i in range(5):
            self.client.post(reverse("admissions:enquiry"), {})
        r = self.client.post(reverse("admissions:enquiry"), VALID)
        self.assertEqual(AdmissionEnquiry.objects.count(), 0)
        self.assertContains(r, "Too many submissions")

    def test_program_prefill_from_query(self):
        p = Program.objects.get(slug="beginner-shooting-program")
        r = self.client.get(reverse("admissions:enquiry") + "?program=" + p.slug)
        self.assertEqual(r.context["form"].initial["program"], p.pk)

    def test_unpublished_program_not_selectable(self):
        p = Program.objects.first()
        p.is_published = False
        p.save()
        form = AdmissionEnquiryForm({**VALID, "program": p.pk})
        self.assertIn("program", form.errors)


class ContactTests(BaseTest):
    DATA = {"name": "Meera", "email": "m@example.com", "phone": "", "subject": "Timings", "message": "What are the batch timings?", "consent": "on"}

    def test_valid_message_saved(self):
        r = self.client.post(reverse("contact:contact"), self.DATA)
        self.assertRedirects(r, reverse("contact:thanks"))
        self.assertEqual(ContactMessage.objects.get().status, "new")

    def test_invalid_shows_errors(self):
        r = self.client.post(reverse("contact:contact"), {**self.DATA, "message": "short", "email": "bad"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(r, "field-error")

    def test_optional_phone_validated(self):
        r = self.client.post(reverse("contact:contact"), {**self.DATA, "phone": "123"})
        self.assertIn("phone", r.context["form"].errors)

    def test_duplicate_message_blocked(self):
        self.client.post(reverse("contact:contact"), self.DATA)
        r = self.client.post(reverse("contact:contact"), self.DATA)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertContains(r, "already received")


class NotificationTests(BaseTest):
    @override_settings(ENQUIRY_NOTIFY_EMAILS=["staff@example.com"])
    def test_staff_and_applicant_emails_sent(self):
        from django.core import mail

        self.client.post(reverse("admissions:enquiry"), VALID)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["staff@example.com"])
        self.assertIn("Aarav Sharma", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[1].to, ["aarav@example.com"])
        self.assertIn("Namaste Aarav Sharma", mail.outbox[1].body)
        self.assertIn("info@rudrasports.com", mail.outbox[1].body)

    def test_only_applicant_acknowledged_when_staff_email_unset(self):
        from django.core import mail

        self.client.post(reverse("admissions:enquiry"), VALID)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["aarav@example.com"])

    def test_no_acknowledgement_without_email(self):
        from django.core import mail

        from .utils import acknowledge

        acknowledge("", "Subject", "Name", "Body")
        self.assertEqual(len(mail.outbox), 0)


class ExtraContentTests(BaseTest):
    def test_announcement_bar(self):
        from .models import Announcement

        self.assertNotContains(self.client.get("/"), 'id="announce"')
        Announcement.objects.create(text="Admissions open for the new batch", link_label="Enquire", link="/admission/")
        r = self.client.get("/about/")
        self.assertContains(r, "Admissions open for the new batch")
        self.assertContains(r, 'href="/admission/"')
        Announcement.objects.update(is_published=False)
        self.assertNotContains(self.client.get("/"), 'id="announce"')

    def test_testimonials_hidden_until_published(self):
        from .models import Testimonial

        t = Testimonial.objects.create(name="Parent A", quote="Great coaching.")
        self.assertFalse(Testimonial._meta.get_field("is_published").default)
        self.assertNotContains(self.client.get("/"), "Great coaching.")
        t.is_published = True
        t.save()
        self.assertContains(self.client.get("/"), "Great coaching.")

    def test_faq_on_home_and_admission(self):
        from .models import Faq

        self.assertNotContains(self.client.get("/admission/"), "faqAccordion")
        Faq.objects.create(question="What should I bring?", answer="Comfortable clothes.")
        self.assertContains(self.client.get("/admission/"), "What should I bring?")
        self.assertContains(self.client.get("/"), "Comfortable clothes.")

    def test_imageless_slides_show_logo_plate(self):
        r = self.client.get("/")
        self.assertContains(r, "hero__plate-wrap")
        self.assertNotContains(r, 'class="hero__bg"')


class AdminPermissionTests(BaseTest):
    def setUp(self):
        super().setUp()
        call_command("create_staff_groups", verbosity=0)
        AdmissionEnquiry.objects.create(applicant_name="X", email="x@example.com", mobile="9876543210", consent=True)
        self.admin = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.editor = User.objects.create_user("editor", password="pass-12345-xyz", is_staff=True)
        self.editor.groups.add(Group.objects.get(name="Content Editors"))
        self.manager = User.objects.create_user("manager", password="pass-12345-xyz", is_staff=True)
        self.manager.groups.add(Group.objects.get(name="Enquiry Managers"))
        self.visitor = User.objects.create_user("visitor", password="pass-12345-xyz")

    def test_anonymous_redirected_to_login(self):
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_non_staff_cannot_enter_admin(self):
        self.client.login(username="visitor", password="pass-12345-xyz")
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_superuser_manages_everything(self):
        self.client.force_login(self.admin)
        for url in [
            "admissions/admissionenquiry", "contact/contactmessage", "programs/program",
            "gallery/galleryimage", "gallery/category", "achievements/achievement",
            "events/event", "core/facility", "core/legalpage", "core/heroslide", "core/announcement", "core/testimonial", "core/faq",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(f"/admin/{url}/").status_code, 200)
        self.assertEqual(self.client.get("/admin/core/sitesettings/", follow=True).status_code, 200)

    def test_editor_cannot_see_enquiries(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get("/admin/programs/program/").status_code, 200)
        self.assertEqual(self.client.get("/admin/admissions/admissionenquiry/").status_code, 403)

    def test_manager_can_update_status_but_not_add_or_delete(self):
        self.client.force_login(self.manager)
        e = AdmissionEnquiry.objects.get()
        self.assertEqual(self.client.get("/admin/admissions/admissionenquiry/").status_code, 200)
        self.assertEqual(self.client.get("/admin/admissions/admissionenquiry/add/").status_code, 403)
        self.assertEqual(self.client.get(f"/admin/admissions/admissionenquiry/{e.pk}/delete/").status_code, 403)
        self.assertEqual(self.client.get("/admin/programs/program/").status_code, 403)
        r = self.client.post("/admin/admissions/admissionenquiry/", {
            "action": "mark_contacted", "_selected_action": [e.pk],
        })
        self.assertEqual(r.status_code, 302)
        e.refresh_from_db()
        self.assertEqual(e.status, "contacted")

    def test_admin_can_create_program_with_upload(self):
        self.client.force_login(self.admin)
        r = self.client.post("/admin/programs/program/add/", {
            "title": "Air Rifle Camp", "slug": "air-rifle-camp", "summary": "Camp", "icon": "bi-bullseye",
            "order": 5, "is_published": "on", "image": make_image("camp.jpg"), "image_alt": "Camp", "image_focus": "center",
            "highlights-TOTAL_FORMS": 0, "highlights-INITIAL_FORMS": 0,
            "highlights-MIN_NUM_FORMS": 0, "highlights-MAX_NUM_FORMS": 1000,
        })
        self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["adminform"].form.errors)
        p = Program.objects.get(slug="air-rifle-camp")
        self.assertTrue(p.image.name.startswith("programs/"))


class MigrationSeedTests(TestCase):
    def test_seed_content_present(self):
        self.assertTrue(LegalPage.objects.filter(slug="privacy-policy").exists())
        self.assertTrue(LegalPage.objects.filter(slug="terms-and-conditions").exists())
        self.assertEqual(Category.objects.count(), 4)


class SiteStructureTests(BaseTest):
    def test_twelve_facility_cards(self):
        r = self.client.get(reverse("core:facilities"))
        self.assertEqual(len(r.context["facilities"]), 12)

    def test_programs_two_per_row(self):
        r = self.client.get(reverse("programs:list"))
        self.assertContains(r, '<div class="col-md-6">', count=4)

    def test_no_book_a_slot_in_header_and_no_website_in_footer(self):
        html = self.client.get("/about/").content.decode()
        header = html.split("</header>")[0]
        self.assertNotIn("Book a Slot", header)
        footer = html.split('<footer class="site-footer">')[1]
        self.assertNotIn("rudrasports.com</span>", footer)
        self.assertIn("info@rudrasports.com", footer)
        self.assertIn("Designed &amp; Developed by", footer)
        self.assertIn('href="https://thewebfix.in"', footer)

    def test_about_page_sections(self):
        r = self.client.get("/about/")
        for text in ("Who we are", "Vision &amp; Mission", "pathway", "Core Values", "Why Choose Us", "Training programs"):
            self.assertContains(r, text)

    def test_contact_banner_image_and_single_email(self):
        s = SiteSettings.load()
        s.contact_image = make_image("contact.jpg")
        s.contact_image_alt = "Range"
        s.save()
        r = self.client.get("/contact/")
        self.assertContains(r, "cx-hero__img")
        self.assertContains(r, "mailto:info@rudrasports.com")
        for other in ("support@", "help@", "gmail.com"):
            self.assertNotContains(r, other)

    def test_page_switches(self):
        from apps.gallery.models import Category, GalleryImage

        s = SiteSettings.load()
        urls = {"show_achievements": "/achievements/", "show_events": "/events/", "show_gallery": "/gallery/", "show_booking": "/book/"}
        for flag, url in urls.items():
            self.assertEqual(self.client.get(url).status_code, 200)
            setattr(s, flag, False)
            s.save()
            self.assertEqual(self.client.get(url).status_code, 404, url)
            self.assertNotContains(self.client.get("/about/"), f'href="{url}"')
            self.assertNotIn(url, self.client.get("/sitemap.xml").content.decode())
            setattr(s, flag, True)
            s.save()
        s.show_achievements = False
        s.save()
        self.assertNotContains(self.client.get("/"), "What we work toward")

    def test_gallery_pagination_and_category_filter(self):
        from apps.gallery.models import Category, GalleryImage

        cat_a, cat_b = Category.objects.all()[:2]
        for i in range(14):
            GalleryImage.objects.create(title=f"A{i}", image=make_image(f"a{i}.jpg"), alt_text="a", category=cat_a)
        GalleryImage.objects.create(title="B0", image=make_image("b0.jpg"), alt_text="b", category=cat_b)
        r = self.client.get(reverse("gallery:index"))
        self.assertEqual(len(r.context["images"]), 12)
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 2)
        self.assertContains(r, "Page 1 of 2")
        r2 = self.client.get(reverse("gallery:index") + "?page=2")
        self.assertEqual(len(r2.context["images"]), 3)
        r3 = self.client.get(reverse("gallery:index") + f"?category={cat_b.slug}")
        self.assertEqual(len(r3.context["images"]), 1)
        self.assertEqual(self.client.get(reverse("gallery:index") + "?page=999").status_code, 200)  # clamps, no crash

    def test_events_pagination_keeps_other_list_position(self):
        now = timezone.now()
        for i in range(8):
            Event.objects.create(title=f"Old {i}", start_at=now - timedelta(days=i + 1))
        r = self.client.get(reverse("events:list") + "?past=2")
        self.assertEqual(r.context["past_page"].number, 2)
        self.assertContains(r, "past=1")

    def test_achievements_pagination(self):
        for i in range(11):
            Achievement.objects.create(title=f"Result {i}", is_published=True)
        r = self.client.get(reverse("achievements:list"))
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 2)

    def test_contact_page_redesign_sections(self):
        r = self.client.get("/contact/")
        for text in ("Contact details", "Send us a message", "Quick ways to reach us", "Find us", "Get directions"):
            self.assertContains(r, text)
        self.assertContains(r, "talk about your shooting journey")
        self.assertContains(r, 'data-topic="Admission enquiry"')

    def test_contact_page_shows_faqs_when_present(self):
        from .models import Faq

        self.assertNotContains(self.client.get("/contact/"), "faqAccordion")
        Faq.objects.create(question="Do you teach juniors?", answer="Yes, see the Junior program.")
        self.assertContains(self.client.get("/contact/"), "Do you teach juniors?")

    def test_admission_form_is_sectioned(self):
        r = self.client.get(reverse("admissions:enquiry"))
        for text in ("Applicant details", "Parent / guardian", "How can we reach you?", "Training interest"):
            self.assertContains(r, text)


class AdmissionFormCompletenessTests(BaseTest):
    def test_all_expected_fields_are_on_the_form(self):
        r = self.client.get(reverse("admissions:enquiry"))
        for field in ("applicant_name", "date_of_birth", "gender", "city", "institution", "guardian_name", "guardian_mobile", "mobile",
                      "email", "preferred_contact", "program", "shooting_interest", "experience_level", "preferred_time", "how_heard", "message", "consent"):
            self.assertContains(r, f'name="{field}"')

    def test_required_fields_server_side(self):
        for missing in ("applicant_name", "date_of_birth", "city", "mobile", "email", "shooting_interest", "experience_level", "consent"):
            data = {k: v for k, v in VALID.items() if k != missing}
            form = AdmissionEnquiryForm(data)
            self.assertFalse(form.is_valid(), missing)
            self.assertIn(missing, form.errors)

    def test_optional_fields_can_be_blank(self):
        for optional in ("gender", "institution", "program", "preferred_time", "how_heard", "message"):
            form = AdmissionEnquiryForm({**VALID, optional: ""})
            self.assertTrue(form.is_valid(), (optional, form.errors))

    def test_invalid_choices_rejected(self):
        for field, bad in (("shooting_interest", "25m_rifle"), ("experience_level", "expert"), ("gender", "x"), ("preferred_time", "night")):
            self.assertIn(field, AdmissionEnquiryForm({**VALID, field: bad}).errors)

    def test_saved_and_visible_in_admin_with_labels(self):
        self.client.post(reverse("admissions:enquiry"), {**VALID, "gender": "female", "preferred_time": "evening", "how_heard": "social", "institution": "Oxford, Class 9"})
        e = AdmissionEnquiry.objects.get()
        self.assertEqual((e.shooting_interest, e.experience_level, e.city, e.gender), ("10m_air_rifle", "beginner", "Indore", "female"))
        admin = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.client.force_login(admin)
        detail = self.client.get(f"/admin/admissions/admissionenquiry/{e.pk}/change/")
        for text in ("10M Air Rifle", "Evening", "Social media", "Oxford, Class 9", "Indore"):
            self.assertContains(detail, text)
        csv = self.client.post("/admin/admissions/admissionenquiry/", {"action": "export_csv", "_selected_action": [e.pk]}).content.decode("utf-8")
        self.assertIn("10M Air Rifle", csv)
        self.assertNotIn("10m_air_rifle", csv)


class HomeEventsSectionTests(BaseTest):
    def test_events_section_hidden_without_upcoming_events(self):
        home = self.client.get("/").content.decode()
        self.assertNotIn("Upcoming on the calendar", home)
        self.assertNotIn("No upcoming events", home)
        Event.objects.create(title="Past Cup", start_at=timezone.now() - timedelta(days=5))
        self.assertNotIn("Upcoming on the calendar", self.client.get("/").content.decode())  # past events alone do not count
        Event.objects.create(title="Draft Cup", start_at=timezone.now() + timedelta(days=5), is_published=False)
        self.assertNotIn("Upcoming on the calendar", self.client.get("/").content.decode())

    def test_events_section_appears_with_an_upcoming_event_and_events_page_keeps_empty_state(self):
        self.assertContains(self.client.get("/events/"), "No upcoming events at the moment")
        Event.objects.create(title="Spring Cup", start_at=timezone.now() + timedelta(days=9))
        home = self.client.get("/")
        self.assertContains(home, "Upcoming on the calendar")
        self.assertContains(home, "Spring Cup")


class AboutVisionMissionTests(BaseTest):
    def test_vision_and_mission_are_matching_paragraphs(self):
        r = self.client.get("/about/")
        html = r.content.decode()
        vision = SiteSettings.load().vision_text
        mission = SiteSettings.load().mission_text
        self.assertRegex(html, r'<p class="quote-block mb-0 mt-3">\s*' + re.escape(vision))
        self.assertRegex(html, r'<p class="quote-block mb-0 mt-3">\s*' + re.escape(mission))
        self.assertEqual(html.count('class="quote-block mb-0 mt-3"'), 2)
        block = html.split("Our Mission")[1].split("</section>")[0]
        self.assertNotIn("check-list", block)  # no bullet list: same paragraph format as the vision
        self.assertNotIn(mission, html.split("Our Vision")[0])  # mission wording is not repeated higher on the page

    def test_mission_text_editable_in_settings(self):
        s = SiteSettings.load()
        s.mission_text = "A brand new mission paragraph."
        s.save()
        self.assertContains(self.client.get("/about/"), "A brand new mission paragraph.")
