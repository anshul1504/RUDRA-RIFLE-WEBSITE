from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStamped
from apps.core.utils import optimise_image
from apps.core.validators import validate_image_upload


class Program(TimeStamped):
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True, help_text="Generated from the title if left blank.")
    summary = models.CharField(max_length=240, help_text="One or two sentences shown on cards.")
    description = models.TextField(blank=True, help_text="Longer description for the detail page. Blank line = new paragraph.")
    icon = models.CharField(max_length=40, default="bi-bullseye", help_text="Bootstrap Icons class, e.g. bi-bullseye.")
    image = models.ImageField(upload_to="programs/", blank=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=200, blank=True, help_text="Describe the photo for screen readers.")
    image_focus = models.CharField(
        "Photo focus", max_length=10, default="center",
        choices=[("top", "Top (show faces of tall / portrait photos)"), ("upper", "Upper part"), ("center", "Centre")],
        help_text="Which part of the photo stays visible when it is cropped into a card.",
    )

    # Only displayed when the academy supplies them - never invented.
    fees = models.CharField(max_length=120, blank=True, help_text="Leave blank to hide.")
    batch_timings = models.CharField(max_length=200, blank=True, help_text="Leave blank to hide.")
    age_eligibility = models.CharField(max_length=120, blank=True, help_text="Leave blank to hide.")
    duration = models.CharField(max_length=120, blank=True, help_text="Leave blank to hide.")

    allow_booking = models.BooleanField(
        "Offer slot booking", default=False,
        help_text="Shows a 'Book a slot' button on this program (used for Pay and Play).",
    )
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "program"
            slug, n = base, 2
            while Program.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        optimise_image(self.image)
        super().save(*args, **kwargs)

    @property
    def focus_css(self):
        return {"top": "50% 0%", "upper": "50% 20%"}.get(self.image_focus, "50% 50%")

    def get_absolute_url(self):
        return reverse("programs:detail", args=[self.slug])

    @property
    def has_details(self):
        return any([self.fees, self.batch_timings, self.age_eligibility, self.duration])

    @property
    def detail_rows(self):
        rows = [
            ("Eligibility", self.age_eligibility),
            ("Duration", self.duration),
            ("Batch timings", self.batch_timings),
            ("Fees", self.fees),
        ]
        return [(label, value) for label, value in rows if value]


class ProgramHighlight(models.Model):
    """A bullet in the 'what's included' list of a program."""

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="highlights")
    text = models.CharField(max_length=160)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text
