from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStamped
from apps.core.utils import optimise_image
from apps.core.validators import validate_image_upload


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or "category"
        super().save(*args, **kwargs)


class GalleryImage(TimeStamped):
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to="gallery/", validators=[validate_image_upload])
    alt_text = models.CharField(max_length=200, help_text="Describe the photo for screen readers.")
    caption = models.CharField(max_length=240, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="images")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        optimise_image(self.image)
        super().save(*args, **kwargs)
