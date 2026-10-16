"""Load the academy's own photographs from the `original_photos/` folder into the website.

File names decide where each photo goes (jpg / jpeg / png / webp):

  slide-1 ... slide-6        homepage carousel slides, in order
  about                      About image (home + About page)
  hero                       plain hero image (used only when the carousel is empty)
  beginner, advanced, junior, pay-and-play      program photos
  gallery-<category>-<n>     gallery photo, e.g. gallery-training-1.jpg, gallery-events-2.jpg
                             (<category> = training / range-facilities / events / shooters; otherwise the first category)

Existing images in those slots are replaced. Edit alt text and captions afterwards in Django Admin.
"""
import re

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.core.models import HeroSlide, SiteSettings
from apps.gallery.models import Category, GalleryImage
from apps.programs.models import Program

EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALT = "Photo from Rudra Sports Rifle Shooting Society, Indore"


class Command(BaseCommand):
    help = "Load photos from original_photos/ into carousel, About, programs and gallery."

    def save_field(self, obj, field, path):
        with open(path, "rb") as fh:
            getattr(obj, field).save(path.name, File(fh), save=False)

    def handle(self, *args, **options):
        folder = settings.BASE_DIR / "original_photos"
        if not folder.is_dir():
            self.stderr.write("Create the original_photos/ folder and put the photos in it (see this command's docstring).")
            return
        files = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXTS)
        if not files:
            self.stderr.write("original_photos/ has no .jpg/.png/.webp files yet.")
            return
        done = 0
        site = SiteSettings.load()
        slides = list(HeroSlide.objects.order_by("order", "id"))
        categories = {c.slug: c for c in Category.objects.all()}
        for path in files:
            stem = path.stem.lower()
            m = re.fullmatch(r"slide-(\d+)", stem)
            if m:
                i = int(m.group(1)) - 1
                slide = slides[i] if i < len(slides) else HeroSlide(headline="New slide", order=i, is_published=False)
                self.save_field(slide, "image", path)
                slide.image_alt = slide.image_alt if slide.image_alt and not slide.image_alt.startswith("Illustration") else ALT
                slide.save()
            elif stem in {"about", "hero"}:
                self.save_field(site, f"{stem}_image", path)
                setattr(site, f"{stem}_image_alt", ALT)
                site.save()
            elif Program.objects.filter(slug=stem).exists():
                program = Program.objects.get(slug=stem)
                self.save_field(program, "image", path)
                program.image_alt = ALT
                program.save()
            elif stem.startswith("gallery-"):
                parts = stem.split("-")[1:]
                slug = "-".join(parts[:-1]) if len(parts) > 1 else ""
                category = categories.get(slug) or next(iter(categories.values()), None)
                if category is None:
                    category = Category.objects.create(name="Gallery")
                    categories[category.slug] = category
                img = GalleryImage(title=stem.replace("-", " ").title(), alt_text=ALT, category=category)
                self.save_field(img, "image", path)
                img.save()
            else:
                self.stdout.write(f"Skipped {path.name} (name not recognised)")
                continue
            done += 1
            self.stdout.write(f"Loaded {path.name}")
        self.stdout.write(self.style.SUCCESS(f"{done} photo(s) loaded. Now improve alt text/captions in Admin."))
