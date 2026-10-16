from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStamped
from apps.core.utils import optimise_image
from apps.core.validators import validate_image_upload


class Achievement(TimeStamped):
    """A real, documented achievement. Only published records appear on the site."""

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    summary = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True, help_text="Supporting details: who, where, result. Blank line = new paragraph.")
    date = models.DateField(null=True, blank=True)
    athlete_name = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="achievements/", blank=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first within the same year.")
    is_published = models.BooleanField(default=False, help_text="Tick only once the details are verified.")

    class Meta:
        ordering = ["-date", "order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "achievement"
            slug, n = base, 2
            while Achievement.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        optimise_image(self.image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("achievements:detail", args=[self.slug])
