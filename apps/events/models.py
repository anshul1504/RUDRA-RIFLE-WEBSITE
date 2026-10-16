from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import TimeStamped
from apps.core.utils import optimise_image
from apps.core.validators import validate_image_upload


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def upcoming(self):
        now = timezone.now()
        return self.published().filter(models.Q(end_at__gte=now) | models.Q(end_at__isnull=True, start_at__gte=now)).order_by("start_at")

    def past(self):
        now = timezone.now()
        return self.published().exclude(
            models.Q(end_at__gte=now) | models.Q(end_at__isnull=True, start_at__gte=now)
        ).order_by("-start_at")


class Event(TimeStamped):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    summary = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True, help_text="Blank line = new paragraph.")
    start_at = models.DateTimeField("Starts")
    end_at = models.DateTimeField("Ends", null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="events/", blank=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=200, blank=True)
    registration_url = models.URLField(
        blank=True, help_text="External registration link. If blank, visitors are sent to the academy's admission enquiry form.",
    )
    is_published = models.BooleanField(default=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["-start_at"]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValidationError({"end_at": "The end must be after the start."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "event"
            slug, n = base, 2
            while Event.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        optimise_image(self.image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.slug])

    @property
    def is_upcoming(self):
        now = timezone.now()
        return (self.end_at or self.start_at) >= now


class EventPhoto(TimeStamped):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="events/photos/", validators=[validate_image_upload])
    alt_text = models.CharField(max_length=200)
    caption = models.CharField(max_length=240, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.event.title} photo {self.pk}"

    def save(self, *args, **kwargs):
        optimise_image(self.image)
        super().save(*args, **kwargs)
