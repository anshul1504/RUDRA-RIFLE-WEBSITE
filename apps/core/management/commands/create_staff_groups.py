"""Create the two standard staff groups with sensible Django permissions.

  Content Editors   - manage programs, gallery, achievements, events, facilities, legal pages, page text, slots, site settings
  Enquiry Managers  - view / update admission enquiries, contact messages and slot bookings (no delete)

Safe to run repeatedly.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

CONTENT = {
    "core": ["sitesettings", "facility", "legalpage", "contentitem", "heroslide", "announcement", "testimonial", "faq", "instagramreel"],
    "bookings": ["slot", "slotschedule"],
    "programs": ["program", "programhighlight"],
    "gallery": ["category", "galleryimage"],
    "achievements": ["achievement"],
    "events": ["event", "eventphoto"],
}
ENQUIRIES = {"admissions": ["admissionenquiry"], "contact": ["contactmessage"], "bookings": ["slotbooking"]}


def perms_for(spec, actions):
    q = Permission.objects.none()
    for app, models in spec.items():
        for model in models:
            codenames = [f"{a}_{model}" for a in actions]
            q = q | Permission.objects.filter(content_type__app_label=app, codename__in=codenames)
    return q


class Command(BaseCommand):
    help = "Create / refresh the 'Content Editors' and 'Enquiry Managers' staff groups."

    def handle(self, *args, **options):
        editors, _ = Group.objects.get_or_create(name="Content Editors")
        editors.permissions.set(perms_for(CONTENT, ["add", "change", "delete", "view"]))
        managers, _ = Group.objects.get_or_create(name="Enquiry Managers")
        managers.permissions.set(perms_for(ENQUIRIES, ["view", "change"]))
        self.stdout.write(self.style.SUCCESS("Staff groups created/updated."))
        self.stdout.write("Assign users to a group in Admin > Users, and tick 'Staff status' so they can log in.")
