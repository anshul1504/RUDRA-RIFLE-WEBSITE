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
    # ---- first six = homepage gallery preview: none of them is used elsewhere on the homepage
    "inauguration-bouquet": ("Inauguration ceremony: bouquet presentation", "The opening of the academy at Oxford International College",
                             "Guests presenting a bouquet and a plant during the academy's inauguration ceremony", "Events"),
    "inauguration-hall": ("Inauguration ceremony: guests in the hall", "Well-wishers gathered in the academy hall",
                          "Guests and well-wishers standing in front of the shooting equipment table in the academy hall", "Events"),
    "inauguration-first-shot": ("Inauguration ceremony: trying the air pistol", "A guest takes aim during the opening",
                                "A guest in a yellow kurta aiming an air pistol during the inauguration, with other guests watching", "Events"),
    "inauguration-guests": ("Inauguration ceremony: guests greeting", "Greetings and celebration on opening day",
                            "Guests greeting each other near a rangoli and balloon decorations at the academy opening", "Events"),
    "range-reception": ("Reception and seating area", "Visitors waiting inside the range hall",
                        "Visitors seated near the Rudra Sports reception desk inside the range hall", "Range & Facilities"),
    "inauguration-group": ("The academy team and guests", "Group photograph at the inauguration",
                           "Guests and the academy team standing together in front of the Rudra Sports banner", "Events"),
    # ---- remaining photos
    "range-firing-line": ("Six lanes, one target wall", "Numbered lanes facing the targets",
                          "The firing line with six numbered lanes, air rifles on the counter and the Rudra Sports target wall behind", "Range & Facilities"),
    "inauguration-equipment-table": ("Guests at the equipment table", "Well-wishers behind the rifles on opening day",
                                     "Guests standing together behind a table of air rifles, tools and flowers at the academy", "Events"),
    "range-registration-desk": ("Registration desk", "The front desk at the academy",
                                "A staff member at the Rudra Sports registration desk, decorated with flowers and balloons", "Range & Facilities"),
    "inauguration-felicitation": ("Inauguration ceremony: felicitation", "Guests exchanging a memento at the inauguration",
                                  "Seven guests standing together as a memento is presented in front of the Rudra Sports banner", "Events"),
    "training-coach-pistol": ("Coach guiding a student", "Pistol stance demonstration at the range",
                              "A coach demonstrating the pistol stance to a student while other students watch", "Training"),
    "training-rifle-session": ("Rifle demonstration for students", "A coach shows how to aim an air rifle",
                               "A coach demonstrating how to aim an air rifle while students in uniform watch", "Training"),
    "range-olympic-rings": ("The range hall", "Olympic rings painted along the hall wall",
                            "The academy's range hall with Olympic rings painted on the wall and shooter artwork at the far end", "Range & Facilities"),
    "range-lanes": ("The firing line", "Numbered lanes under the Rudra Sports banner",
                    "An empty firing line with numbered lanes and the Rudra Sports banner on the wall", "Range & Facilities"),
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
RETIRED = ["inauguration-memento"]  # replaced by a better frame of the same moment; removed so nothing looks duplicated

# homepage carousel, in slide order
SLIDES = [
    ("range-firing-line", "The firing line with six numbered lanes, air rifles on the counter and the Rudra Sports target wall behind"),
    ("training-class-seated", "School students seated on the floor listening to a coach in front of the firing line"),
    ("range-lanes", "An empty firing line with numbered lanes and the Rudra Sports banner on the wall"),
    ("training-students-line", "School students in uniform standing in a line inside the range hall"),
]
PROGRAMS = {
    "beginner-shooting-program": ("training-coach-pistol", "A coach demonstrating the pistol stance to a student while other students watch", "center"),
    "junior-shooter-development-program": ("training-kids-pistol", "Young students taking aim with air pistols at the firing line with a coach beside them", "center"),
    "advanced-competitive-training": ("shooter-boy-air-rifle", "A student aiming an air rifle at the firing line", "center"),
    "pay-and-play": ("training-rifle-session", "A coach demonstrating how to aim an air rifle while students in uniform watch", "center"),
}
SITE = {  # SiteSettings field -> (photo, alt)
    "hero_image": ("range-olympic-rings", "The academy's range hall with Olympic rings painted on the wall"),
    "about_image": ("inauguration-felicitation", "Seven guests standing together as a memento is presented in front of the Rudra Sports banner"),
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

        # gallery: drop old placeholders and retired photos, then add / update each photo once (matched by file name)
        for old in GalleryImage.objects.filter(caption="Sample photo - to be replaced"):
            old.image.delete(save=False)
            old.delete()
        for stem in RETIRED:
            for old in GalleryImage.objects.filter(image__startswith=f"gallery/{stem}"):
                old.image.delete(save=False)
                old.delete()
        cats = {}
        for order, (stem, (title, caption, alt, cat_name)) in enumerate(GALLERY.items()):
            cat = cats.get(cat_name) or Category.objects.get_or_create(name=cat_name, defaults={"order": 10 + len(cats)})[0]
            cats[cat_name] = cat
            img = GalleryImage.objects.filter(image__startswith=f"gallery/{stem}").first() or GalleryImage.objects.filter(title=title).first()
            created = img is None
            if created:
                img = GalleryImage(title=title)
            if created or refresh or not img.image or Path(img.image.name).stem.split("_")[0] != stem:
                self.attach(img, "image", stem, True)
            img.title, img.alt_text, img.caption, img.category, img.order = title, alt, caption, cat, order
            img.save()
            done += created

        for slide, (stem, alt) in zip(HeroSlide.objects.order_by("order", "id"), SLIDES):
            self.attach(slide, "image", stem, refresh)
            slide.image_alt = alt
            slide.save()
        for slug, (stem, alt, focus) in PROGRAMS.items():
            program = Program.objects.filter(slug=slug).first()
            if program:
                self.attach(program, "image", stem, refresh)
                program.image_alt = alt
                program.image_focus = focus
                program.save()
        site = SiteSettings.load()
        for field, (stem, alt) in SITE.items():
            self.attach(site, field, stem, refresh)
            setattr(site, f"{field}_alt", alt)
        site.save()
        self.stdout.write(self.style.SUCCESS(
            f"Gallery: {GalleryImage.objects.count()} photos ({done} new). Carousel, About, Contact banner and program cards updated."))
