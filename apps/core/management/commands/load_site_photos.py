"""Load the academy's own photographs (site_photos/) into the website.

The photos come from the academy's shared Drive folder "Rudra Sports Images": inauguration, range and training
pictures. Near-duplicates were removed, so every photo is a different moment. Each photo is placed once in the gallery
and the strongest ones also feed the homepage carousel, About page, program cards and Contact banner.

Safe to re-run: gallery entries are matched by title, other slots are simply re-attached. Use --refresh to re-save the
image files. Edit titles, captions and alt text afterwards in Django Admin.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.core.models import HeroSlide, SiteSettings
from apps.gallery.models import Category, GalleryImage
from apps.programs.models import Program

PHOTOS = Path(settings.BASE_DIR) / "site_photos"

# file stem -> (gallery title, caption, alt text, category)
GALLERY = {
    # ---- first six are not used elsewhere on the homepage, so the homepage gallery preview never repeats a hero/program photo
    "inauguration-bouquet": ("Inauguration ceremony: bouquet presentation", "The opening of the academy at Oxford International College",
                             "Guests presenting a bouquet and a plant during the academy's inauguration ceremony", "Events"),
    "inauguration-memento": ("Inauguration ceremony: memento presentation", "Guests exchanging a memento at the inauguration",
                             "Guests exchanging a memento in front of the Rudra Sports banner at the inauguration", "Events"),
    "inauguration-hall": ("Inauguration ceremony: guests in the hall", "Well-wishers gathered in the academy hall",
                          "Guests and well-wishers standing in front of the shooting equipment table in the academy hall", "Events"),
    "inauguration-first-shot": ("Inauguration ceremony: trying the air pistol", "A guest takes aim during the opening",
                                "A guest in a yellow kurta aiming an air pistol during the inauguration, with other guests watching", "Events"),
    "inauguration-guests": ("Inauguration ceremony: guests greeting", "Greetings and celebration on opening day",
                            "Guests greeting each other near a rangoli and balloon decorations at the academy opening", "Events"),
    "training-coach-pistol": ("Coach guiding a student", "Pistol stance demonstration at the range",
                              "A coach demonstrating the pistol stance to a student at the shooting range", "Training"),
    # ---- remaining photos
    "training-rifle-session": ("Rifle practice under supervision", "A student at the firing line with a coach nearby",
                               "A student in school uniform aiming an air rifle while a coach supervises", "Training"),
    "inauguration-group": ("The academy team and guests", "Group photograph at the inauguration",
                           "Guests and the academy team standing together in front of the Rudra Sports banner", "Events"),
    "range-olympic-rings": ("The range hall", "Olympic rings painted along the hall wall",
                            "The academy's range hall with Olympic rings painted on the wall and shooter artwork at the far end", "Range & Facilities"),
    "range-lanes": ("The firing line", "Numbered lanes under the Rudra Sports banner",
                    "An empty firing line with numbered lanes and the Rudra Sports banner on the wall", "Range & Facilities"),
    "range-reception": ("Reception and seating area", "Visitors waiting inside the range hall",
                        "Visitors seated near the Rudra Sports reception desk inside the range hall", "Range & Facilities"),
    "training-students-line": ("Students ready for a session", "School students lined up inside the range hall",
                               "School students in uniform standing in a line inside the range hall", "Training"),
    "training-class-seated": ("Students listening to a briefing", "A coach addressing students before practice",
                              "School students seated on the floor listening to a coach in front of the firing line", "Training"),
    "training-coach-guidance": ("Coach guiding a young shooter", "Hands-on guidance at the firing line",
                                "A coach adjusting a young student's position while other students watch", "Training"),
    "training-kids-pistol": ("Young shooters on the line", "Students taking aim with a coach beside them",
                             "Young students taking aim with air pistols at the firing line with a coach beside them", "Training"),
    "shooter-woman-rifle": ("Air rifle practice", "Focus and form at the firing line",
                            "A woman wearing red ear defenders aiming an air rifle at the range", "Shooters"),
    "shooter-boy-air-rifle": ("Young shooter with an air rifle", "A student takes aim",
                              "A student aiming an air rifle at the firing line", "Shooters"),
    "press-coverage": ("In the news: academy launch", "Newspaper coverage of the academy's grand opening",
                       "Newspaper clipping reporting the grand opening of Rudra Sports Rifle Shooting Academy", "In the News"),
}

# homepage carousel, in slide order
SLIDES = [
    ("range-olympic-rings", "The academy's range hall with Olympic rings painted on the wall"),
    ("training-class-seated", "School students seated on the floor listening to a coach in front of the firing line"),
    ("range-lanes", "An empty firing line with numbered lanes and the Rudra Sports banner on the wall"),
    ("training-students-line", "School students in uniform standing in a line inside the range hall"),
]
PROGRAMS = {
    "beginner-shooting-program": ("training-coach-guidance", "A coach adjusting a young student's position while other students watch"),
    "junior-shooter-development-program": ("training-kids-pistol", "Young students taking aim with air pistols at the firing line with a coach beside them"),
    "advanced-competitive-training": ("shooter-boy-air-rifle", "A student aiming an air rifle at the firing line"),
    "pay-and-play": ("shooter-woman-rifle", "A woman wearing red ear defenders aiming an air rifle at the range"),
}
SITE = {  # SiteSettings field -> (photo, alt)
    "hero_image": ("range-olympic-rings", "The academy's range hall with Olympic rings painted on the wall"),
    "about_image": ("inauguration-group", "Guests and the academy team standing together in front of the Rudra Sports banner"),
    "contact_image": ("range-reception", "Visitors seated near the Rudra Sports reception desk inside the range hall"),
}


class Command(BaseCommand):
    help = "Load the academy's own photographs into the gallery, carousel, About, programs and Contact banner."

    def add_arguments(self, parser):
        parser.add_argument("--refresh", action="store_true", help="Re-save image files that are already attached.")

    def attach(self, obj, field, stem, refresh):
        current = getattr(obj, field)
        if current and not refresh and Path(current.name).stem.split("_")[0] == stem:
            return False
        if current:
            current.delete(save=False)
        with open(PHOTOS / f"{stem}.jpg", "rb") as fh:
            getattr(obj, field).save(f"{stem}.jpg", File(fh), save=False)
        return True

    def handle(self, *args, **opts):
        refresh = opts["refresh"]
        missing = [s for s in GALLERY if not (PHOTOS / f"{s}.jpg").exists()]
        if missing:
            self.stderr.write(f"Missing files in site_photos/: {missing}")
            return
        done = 0

        # gallery: remove only the old placeholder entries, then add each photo once
        for old in GalleryImage.objects.filter(caption="Sample photo - to be replaced"):
            old.image.delete(save=False)
            old.delete()
        cats = {}
        for order, (stem, (title, caption, alt, cat_name)) in enumerate(GALLERY.items()):
            cat = cats.get(cat_name) or Category.objects.get_or_create(name=cat_name, defaults={"order": 10 + len(cats)})[0]
            cats[cat_name] = cat
            img, created = GalleryImage.objects.get_or_create(title=title, defaults={"alt_text": alt, "caption": caption, "category": cat, "order": order})
            if created or refresh or not img.image:
                self.attach(img, "image", stem, True)
            img.alt_text, img.caption, img.category, img.order = alt, caption, cat, order
            img.save()
            done += created

        for slide, (stem, alt) in zip(HeroSlide.objects.order_by("order", "id"), SLIDES):
            self.attach(slide, "image", stem, refresh)
            slide.image_alt = alt
            slide.save()
        for slug, (stem, alt) in PROGRAMS.items():
            program = Program.objects.filter(slug=slug).first()
            if program:
                self.attach(program, "image", stem, refresh)
                program.image_alt = alt
                program.save()
        site = SiteSettings.load()
        for field, (stem, alt) in SITE.items():
            self.attach(site, field, stem, refresh)
            setattr(site, f"{field}_alt", alt)
        site.save()
        self.stdout.write(self.style.SUCCESS(
            f"Gallery: {GalleryImage.objects.count()} photos ({done} new). Carousel, About, Contact banner and program cards updated."))
