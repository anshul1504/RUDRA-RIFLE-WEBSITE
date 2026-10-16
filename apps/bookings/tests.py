from datetime import time, timedelta

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import ContentItem, SiteSettings
from apps.programs.models import Program

from .models import Slot, SlotBooking, SlotSchedule

DATA = {"name": "Rohan Verma", "mobile": "98765 43210", "email": "", "participants": 1, "experience_level": "beginner", "shooting_type": "10m_air_rifle", "message": "", "consent": "on"}


def make_slot(days=2, capacity=3, **kw):
    day = timezone.localdate() + timedelta(days=days)
    return Slot.objects.create(date=day, start_time=time(6, 0), end_time=time(7, 0), capacity=capacity, **kw)


class SeedTests(TestCase):
    def test_pay_and_play_program_seeded(self):
        p = Program.objects.get(slug="pay-and-play")
        self.assertTrue(p.allow_booking)
        self.assertEqual(p.fees, "")  # nothing invented
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "Book a slot")
        self.assertContains(self.client.get(reverse("programs:list")), "Pay and Play")

    def test_other_programs_not_bookable(self):
        self.assertNotContains(self.client.get("/programs/beginner-shooting-program/"), "Book a slot")


class PublicBookingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_empty_state(self):
        self.assertContains(self.client.get(reverse("bookings:slots")), "No slots are open right now")

    def test_list_shows_only_open_future_slots(self):
        open_slot = make_slot(2, title="Open one")
        make_slot(3, title="Closed one", is_published=False)
        make_slot(-1, title="Yesterday slot")
        r = self.client.get(reverse("bookings:slots"))
        self.assertContains(r, "Open one")
        self.assertNotContains(r, "Closed one")
        self.assertNotContains(r, "Yesterday slot")
        self.assertContains(r, reverse("bookings:book", args=[open_slot.pk]))

    def test_slots_listed_in_date_order(self):
        make_slot(5, title="Later")
        make_slot(1, title="Sooner")
        make_slot(3, title="Middle")
        r = self.client.get(reverse("bookings:slots"))
        self.assertEqual([d["slots"][0].title for d in r.context["days"]], ["Sooner", "Middle", "Later"])

    def test_home_shows_next_slots_and_four_programs(self):
        make_slot(1, title="Sooner")
        r = self.client.get("/")
        self.assertContains(r, "Book a practice slot online")
        self.assertContains(r, "Pay and Play")
        self.assertEqual(len(r.context["next_slots"]), 1)

    def test_successful_booking(self):
        slot = make_slot()
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), DATA)
        b = SlotBooking.objects.get()
        self.assertRedirects(r, reverse("bookings:confirmation", args=[b.reference]), fetch_redirect_response=False)
        self.assertEqual(b.mobile, "9876543210")
        self.assertEqual(b.status, "pending")
        self.assertTrue(b.reference.startswith("RSB-"))
        self.assertContains(self.client.get(reverse("bookings:confirmation", args=[b.reference])), b.reference)

    def test_confirmation_not_viewable_without_session(self):
        slot = make_slot()
        b = SlotBooking.objects.create(slot=slot, name="X", mobile="9876543210", consent=True)
        r = self.client.get(reverse("bookings:confirmation", args=[b.reference]))
        self.assertRedirects(r, reverse("bookings:slots"), fetch_redirect_response=False)

    def test_capacity_enforced(self):
        slot = make_slot(capacity=2)
        self.client.post(reverse("bookings:book", args=[slot.pk]), {**DATA, "participants": 2})
        cache.clear()
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), {**DATA, "mobile": "9123456780"})
        self.assertEqual(SlotBooking.objects.count(), 1)
        self.assertContains(r, "now full")
        self.assertTrue(Slot.objects.get(pk=slot.pk).is_full)
        self.assertContains(self.client.get(reverse("bookings:slots")), "Full")

    def test_too_many_participants_rejected(self):
        slot = make_slot(capacity=2)
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), {**DATA, "participants": 3})
        self.assertEqual(SlotBooking.objects.count(), 0)
        self.assertContains(r, "Only 2 seat(s) left")

    def test_cancelled_booking_frees_seats(self):
        slot = make_slot(capacity=1)
        b = SlotBooking.objects.create(slot=slot, name="A", mobile="9876543210", consent=True)
        self.assertTrue(Slot.objects.get(pk=slot.pk).is_full)
        b.status = "cancelled"
        b.save()
        self.assertEqual(Slot.objects.get(pk=slot.pk).seats_left, 1)

    def test_duplicate_mobile_same_slot_blocked(self):
        slot = make_slot()
        self.client.post(reverse("bookings:book", args=[slot.pk]), DATA)
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), DATA)
        self.assertEqual(SlotBooking.objects.count(), 1)
        self.assertContains(r, "already exists")

    def test_past_or_closed_slot_not_bookable(self):
        past = make_slot(-1)
        closed = make_slot(4, is_published=False)
        self.assertEqual(self.client.get(reverse("bookings:book", args=[closed.pk])).status_code, 404)
        r = self.client.post(reverse("bookings:book", args=[past.pk]), DATA)
        self.assertEqual(SlotBooking.objects.count(), 0)
        self.assertIn(r.status_code, (302, 404))

    def test_validation_errors(self):
        slot = make_slot()
        r = self.client.post(reverse("bookings:book", args=[slot.pk]), {"name": "", "mobile": "12", "participants": 0})
        self.assertEqual(r.status_code, 200)
        form = r.context["form"]
        for f in ("name", "mobile", "participants", "consent"):
            self.assertIn(f, form.errors)

    def test_honeypot_and_html_stripped(self):
        slot = make_slot()
        self.client.post(reverse("bookings:book", args=[slot.pk]), {**DATA, "contact_website": "spam"})
        self.assertEqual(SlotBooking.objects.count(), 0)
        self.client.post(reverse("bookings:book", args=[slot.pk]), {**DATA, "message": "<script>x</script>hello"})
        self.assertNotIn("<script>", SlotBooking.objects.get().message)

    def test_end_time_validation(self):
        from django.core.exceptions import ValidationError

        s = Slot(date=timezone.localdate(), start_time=time(8), end_time=time(7), capacity=1)
        with self.assertRaises(ValidationError):
            s.full_clean()


class ScheduleTests(TestCase):
    def test_generate_is_idempotent(self):
        pp = Program.objects.get(slug="pay-and-play")
        sched = SlotSchedule.objects.create(weekday=timezone.localdate().weekday(), start_time=time(6), end_time=time(7), capacity=4, program=pp)
        first = sched.generate(14)
        self.assertGreaterEqual(first, 2)
        self.assertEqual(sched.generate(14), 0)
        self.assertEqual(Slot.objects.filter(program=pp).count(), first)
        self.assertEqual(Slot.objects.first().capacity, 4)


class DatabaseDrivenContentTests(TestCase):
    def test_hero_text_is_editable(self):
        from apps.core.models import HeroSlide

        HeroSlide.objects.update(is_published=False)  # the plain hero is the carousel fallback
        s = SiteSettings.load()
        s.hero_headline = "Aim for"
        s.hero_headline_accent = "Gold."
        s.save()
        r = self.client.get("/")
        self.assertContains(r, "Aim for")
        self.assertContains(r, "Gold.")

    def test_list_items_editable_and_unpublish(self):
        ContentItem.objects.filter(kind="why", title__startswith="Experienced").update(title="Brand New Reason")
        ContentItem.objects.filter(kind="mission", title__startswith="Promote").update(is_published=False)
        home = self.client.get("/")
        self.assertContains(home, "Brand New Reason")
        about = self.client.get("/about/")
        self.assertNotContains(about, "Promote shooting sports among youth")
        self.assertContains(about, "Discipline")

    def test_about_vision_from_settings(self):
        s = SiteSettings.load()
        s.vision_text = "A custom vision statement."
        s.save()
        self.assertContains(self.client.get("/about/"), "A custom vision statement.")

    def test_carousel_renders_published_slides(self):
        from apps.core.models import HeroSlide

        r = self.client.get("/")
        self.assertContains(r, 'id="heroCarousel"')
        self.assertContains(r, "Book your")
        self.assertEqual(r.content.decode().count("<h1"), 1)
        HeroSlide.objects.update(is_published=False)
        r = self.client.get("/")
        self.assertNotContains(r, 'id="heroCarousel"')
        self.assertContains(r, "Train Like a")  # falls back to the static hero

    def test_slide_link_validation(self):
        from django.core.exceptions import ValidationError

        from apps.core.models import HeroSlide

        s = HeroSlide(headline="X", primary_link="javascript:alert(1)")
        with self.assertRaises(ValidationError):
            s.full_clean()
        HeroSlide(headline="X", primary_link="/book/").full_clean()

    def test_domain_emails_and_credit(self):
        s = SiteSettings.load()
        self.assertEqual(s.email, "info@rudrasports.com")
        r = self.client.get("/")
        self.assertContains(r, "Designed &amp; Developed by")
        self.assertContains(r, 'href="https://thewebfix.in"')
        # the credit is fixed in code: no model field to edit
        names = {f.name for f in SiteSettings._meta.get_fields()}
        self.assertFalse({n for n in names if "developer" in n})
        from django.contrib import admin as dj_admin

        self.assertNotIn("developer_credit_url", str(dj_admin.site._registry[SiteSettings].fieldsets))
        from apps.core.models import LegalPage

        self.assertNotIn("gmail.com", LegalPage.objects.get(slug="privacy-policy").body)


class BookingAdminTests(TestCase):
    def setUp(self):
        call_command("create_staff_groups", verbosity=0)
        self.admin = User.objects.create_superuser("root", "r@example.com", "pass-12345-xyz")
        self.manager = User.objects.create_user("mgr", password="pass-12345-xyz", is_staff=True)
        self.manager.groups.add(Group.objects.get(name="Enquiry Managers"))
        self.slot = make_slot(capacity=2)
        self.b = SlotBooking.objects.create(slot=self.slot, name="A", mobile="9876543210", consent=True)

    def test_admin_pages_load(self):
        self.client.force_login(self.admin)
        for path in ["", "bookings/slot/", "bookings/slotbooking/", "bookings/slotschedule/", f"bookings/slot/{self.slot.pk}/change/",
                     f"bookings/slotbooking/{self.b.pk}/change/", "core/contentitem/", "core/sitesettings/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(f"/admin/{path}", follow=True).status_code, 200)

    def test_dashboard_shows_kpis(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/admin/"), "Pending slot bookings")

    def test_confirm_and_cancel_actions(self):
        self.client.force_login(self.admin)
        url = "/admin/bookings/slotbooking/"
        self.client.post(url, {"action": "confirm", "_selected_action": [self.b.pk]})
        self.b.refresh_from_db()
        self.assertEqual(self.b.status, "confirmed")
        self.client.post(url, {"action": "cancel", "_selected_action": [self.b.pk]})
        self.b.refresh_from_db()
        self.assertEqual(self.b.status, "cancelled")

    def test_csv_export(self):
        self.client.force_login(self.admin)
        r = self.client.post("/admin/bookings/slotbooking/", {"action": "export_csv", "_selected_action": [self.b.pk]})
        self.assertEqual(r["Content-Type"].split(";")[0], "text/csv")
        self.assertIn("9876543210", r.content.decode("utf-8"))

    def test_generate_action_in_admin(self):
        self.client.force_login(self.admin)
        sched = SlotSchedule.objects.create(weekday=(timezone.localdate() + timedelta(days=1)).weekday(), start_time=time(9), end_time=time(10), capacity=3)
        self.client.post("/admin/bookings/slotschedule/", {"action": "generate_14", "_selected_action": [sched.pk]})
        self.assertTrue(Slot.objects.filter(start_time=time(9)).exists())

    def test_manager_can_update_bookings_not_slots(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/admin/bookings/slotbooking/").status_code, 200)
        self.assertEqual(self.client.get("/admin/bookings/slot/").status_code, 403)
        self.assertEqual(self.client.get("/admin/bookings/slotbooking/add/").status_code, 403)


class EnquiryAdminTests(TestCase):
    def test_enquiry_admin_list_and_detail(self):
        from apps.admissions.models import AdmissionEnquiry

        e = AdmissionEnquiry.objects.create(applicant_name="Kabir", guardian_name="Rina", email="k@example.com", mobile="9876543210", consent=True)
        admin = User.objects.create_superuser("root2", "r@example.com", "pass-12345-xyz")
        self.client.force_login(admin)
        r = self.client.get("/admin/admissions/admissionenquiry/")
        self.assertContains(r, "tel:+919876543210")
        self.assertContains(r, "wa.me/919876543210")
        r = self.client.get(f"/admin/admissions/admissionenquiry/{e.pk}/change/")
        self.assertContains(r, "Quick contact")
        self.client.post("/admin/admissions/admissionenquiry/", {"action": "mark_closed", "_selected_action": [e.pk]})
        e.refresh_from_db()
        self.assertEqual(e.status, "closed")
        self.client.post("/admin/admissions/admissionenquiry/", {"action": "mark_new", "_selected_action": [e.pk]})
        e.refresh_from_db()
        self.assertEqual(e.status, "new")
        self.assertEqual(self.client.get("/admin/admissions/admissionenquiry/?created_at__gte=2020-01-01").status_code, 200)
