"""Load the academy's short clips (site_videos/) into the Gallery page's Videos section.

Files come from the shared Drive folder. Clips and cover pictures are kept out of git; copy them to site_videos/ and run
this command. Safe to re-run (matched by title). Titles can be edited in Django Admin > Gallery videos.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.gallery.models import GalleryVideo

FOLDER = Path(settings.BASE_DIR) / "site_videos"
CLIPS = [  # file stem -> title
    ("video-01", "Shooter at the firing line"),
    ("video-02", "The range with lanes lit"),
    ("video-03", "Guests trying an air rifle"),
    ("video-04", "Registration desk at the academy"),
    ("video-05", "Guests at the academy opening"),
    ("video-06", "Balloon entrance to the range"),
    ("video-07", "Rifles and equipment on the counter"),
]


class Command(BaseCommand):
    help = "Load the academy's video clips into the Gallery page."

    def handle(self, *args, **opts):
        added = 0
        for order, (stem, title) in enumerate(CLIPS):
            clip, poster = FOLDER / f"{stem}.mp4", FOLDER / f"{stem}.jpg"
            if not clip.exists():
                self.stderr.write(f"Missing {clip.name}: skipped")
                continue
            obj = GalleryVideo.objects.filter(title=title).first()
            created = obj is None
            if created:
                obj = GalleryVideo(title=title)
                with open(clip, "rb") as fh:
                    obj.video.save(clip.name, File(fh), save=False)
            if poster.exists() and (created or not obj.poster):
                with open(poster, "rb") as fh:
                    obj.poster.save(poster.name, File(fh), save=False)
            obj.order = order
            obj.save()
            added += created
        self.stdout.write(self.style.SUCCESS(f"Videos: {GalleryVideo.objects.count()} ({added} new)."))
