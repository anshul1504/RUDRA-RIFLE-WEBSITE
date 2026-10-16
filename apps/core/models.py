from urllib.parse import quote, quote_plus

from django.db import models
from django.urls import reverse

from .utils import optimise_image
from .validators import validate_image_upload, validate_instagram_post_url


# Academy location (supplied by the client): 22.7558407, 75.7659442
DEFAULT_MAP_LINK_URL = "https://www.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en"
DEFAULT_MAP_EMBED_URL = "https://maps.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en&output=embed"


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteSettings(TimeStamped):
    """Single editable record holding contact details and site-wide content."""

    organisation_name = models.CharField(max_length=120, default="Rudra Sports Rifle Shooting Society")
    tagline = models.CharField(max_length=160, blank=True, default="Focus. Aim. Achieve.")
    city = models.CharField(max_length=80, default="Indore")
    state = models.CharField(max_length=80, default="Madhya Pradesh")

    address = models.TextField(
        default="Oxford International College, Opp. Pitra Parvat, Hatod Road, Gandhi Nagar, Indore, Madhya Pradesh",
    )
    phone = models.CharField(max_length=20, default="94250 93128", help_text="Shown on the site and used for click-to-call.")
    whatsapp_number = models.CharField(
        max_length=20, blank=True, default="94250 93128",
        help_text="Number for the WhatsApp enquiry button. Leave blank to hide the button.",
    )
    email = models.EmailField("Email", default="info@rudrasports.com")
    website = models.CharField(max_length=120, blank=True, default="rudrasports.com")

    map_embed_url = models.URLField(
        max_length=1000, blank=True, default=DEFAULT_MAP_EMBED_URL,
        help_text="Google Maps embed URL used in the map frame (iframe src). Default: the academy's coordinates, no API key needed.",
    )
    map_link_url = models.URLField(
        max_length=1000, blank=True, default=DEFAULT_MAP_LINK_URL,
        help_text="Public Google Maps link behind 'Open in Google Maps' / 'Get directions'. If blank, a search link built from the address is used.",
    )
    opening_hours = models.CharField(
        max_length=200, blank=True, help_text="Optional. Shown on the contact page only when filled in.",
    )

    show_achievements = models.BooleanField("Show Achievements page", default=True, help_text="Untick to hide the page, its menu links and the homepage section.")
    show_events = models.BooleanField("Show Events page", default=True)
    show_gallery = models.BooleanField("Show Gallery page", default=True)
    show_booking = models.BooleanField("Show Slot booking", default=True, help_text="Controls /book/, the homepage Pay and Play section and Book a slot buttons.")

    contact_image = models.ImageField(upload_to="site/", blank=True, validators=[validate_image_upload], help_text="Banner photo on the Contact page.")
    contact_image_alt = models.CharField(max_length=200, blank=True)

    hero_image = models.ImageField(
        upload_to="site/", blank=True, validators=[validate_image_upload],
        help_text="Homepage hero photograph (landscape, at least 1600 px wide). A neutral branded background is used until uploaded.",
    )
    hero_image_alt = models.CharField(max_length=200, blank=True)
    about_image = models.ImageField(upload_to="site/", blank=True, validators=[validate_image_upload])
    about_image_alt = models.CharField(max_length=200, blank=True)


    # --- Homepage & page copy (all editable; defaults come from the academy document) ---
    hero_eyebrow = models.CharField(max_length=80, blank=True, default="Indore, Madhya Pradesh")
    hero_headline = models.CharField("Hero headline (first part)", max_length=80, default="Train Like a")
    hero_headline_accent = models.CharField("Hero headline (gold part)", max_length=60, blank=True, default="Champion.")
    hero_subheadline = models.CharField(
        max_length=240, default="Professional Rifle & Pistol Shooting Training for Beginners and Competitive Shooters.",
    )
    hero_tagline = models.CharField(max_length=120, blank=True, default="Aim High. Shoot Right. Build Discipline.")
    hero_primary_cta = models.CharField("Hero primary button", max_length=40, default="Enquire for Admission")
    hero_secondary_cta = models.CharField("Hero secondary button", max_length=40, default="Explore Training Programs")

    intro_heading = models.CharField(max_length=160, default="Discipline, focus, confidence and sportsmanship.")
    about_intro = models.TextField(
        "About the academy (intro)",
        default="Rudra Sports Rifle Shooting Society is a platform dedicated to promoting the sport of rifle and pistol "
                "shooting among youth, sports enthusiasts and aspiring national-level shooters.",
    )
    about_mission_text = models.TextField(
        "Mission paragraph",
        default="Our mission is to develop discipline, focus, confidence and sportsmanship through professional shooting "
                "training under safe and guided supervision. We aim to nurture talent from beginner to competitive level and "
                "encourage participation in district, state and national championships.",
    )
    vision_text = models.TextField(
        "Vision",
        default="To become a leading shooting academy that empowers young shooters with world-class training, modern "
                "facilities and the mindset required to excel in competitive shooting sports.",
    )
    mission_text = models.TextField(
        "Mission (About page paragraph)",
        default="To promote shooting sports among youth and provide professional rifle and pistol shooting training, "
                "developing discipline, concentration and self-confidence in every shooter. We prepare athletes for district, "
                "state and national competitions and encourage fitness, mental strength and sports ethics.",
    )
    safety_heading = models.CharField(max_length=120, default="Safety is our highest priority.")
    safety_text = models.TextField(
        "Safety First statement",
        default="At Rudra Sports Rifle Shooting Society, safety is our highest priority. Every trainee is guided through "
                "proper firearm handling, discipline protocols and supervised practice to ensure responsible sports shooting.",
    )
    responsible_text = models.TextField(
        "Responsible shooting statement (About page)",
        default="Responsible sports shooting means proper firearm handling, clear discipline protocols and supervised "
                "practice at every session.",
    )
    footer_description = models.TextField(
        default="Professional rifle and pistol shooting training for beginners and competitive shooters, under safe and "
                "guided supervision in Indore, Madhya Pradesh.",
    )
    cta_heading = models.CharField(
        "Call-to-action heading", max_length=160,
        default="Begin your journey toward precision, discipline and excellence.",
    )
    cta_text = models.CharField(
        "Call-to-action text", max_length=240,
        default="Become a part of Rudra Sports Rifle Shooting Society. Send an admission enquiry and our team will get back to you.",
    )
    booking_intro = models.TextField(
        "Slot booking page intro", blank=True,
        default="Choose an available practice slot and send a booking request. Our team will confirm it with you.",
    )
    booking_payment_note = models.CharField(
        "Slot booking payment note", max_length=240, blank=True,
        help_text="Shown on the booking page, e.g. how payment is collected. Leave blank to hide.",
    )

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    x_url = models.URLField("X / Twitter URL", blank=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton
        if not self.created_at:
            existing = SiteSettings.objects.filter(pk=1).values_list("created_at", flat=True).first()
            if existing:
                self.created_at = existing
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # the singleton cannot be deleted
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # --- helpers used by templates -------------------------------------
    @staticmethod
    def _digits(number):
        return "".join(ch for ch in number if ch.isdigit())

    @property
    def phone_href(self):
        d = self._digits(self.phone)
        return f"tel:+91{d[-10:]}" if len(d) >= 10 else f"tel:{d}"

    @property
    def whatsapp_href(self):
        d = self._digits(self.whatsapp_number)
        if len(d) < 10:
            return ""
        text = quote(f"Hello, I would like to enquire about training at {self.organisation_name}.")
        return f"https://wa.me/91{d[-10:]}?text={text}"

    @property
    def directions_url(self):
        if self.map_link_url:
            return self.map_link_url
        return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(self.address)

    @property
    def social_links(self):
        pairs = [
            ("Facebook", "bi-facebook", self.facebook_url),
            ("Instagram", "bi-instagram", self.instagram_url),
            ("YouTube", "bi-youtube", self.youtube_url),
            ("X", "bi-twitter-x", self.x_url),
        ]
        return [{"label": label, "icon": icon, "url": url} for label, icon, url in pairs if url]


class Facility(TimeStamped):
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=40, default="bi-bullseye",
        help_text="Bootstrap Icons class, e.g. bi-bullseye (see icons.getbootstrap.com).",
    )
    image = models.ImageField(upload_to="facilities/", blank=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name_plural = "facilities"

    def save(self, *args, **kwargs):
        optimise_image(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LegalPage(TimeStamped):
    PRIVACY = "privacy-policy"
    TERMS = "terms-and-conditions"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    body = models.TextField(
        help_text="Plain text. Blank line = new paragraph. Start a line with '## ' for a heading and '- ' for a bullet.",
    )
    last_reviewed = models.DateField(
        null=True, blank=True,
        help_text="Set once the text has been reviewed by the academy / a legal adviser.",
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:legal", args=[self.slug])


class ContentItem(TimeStamped):
    """Short editable list items used on the About, home and achievements pages."""

    class Kind(models.TextChoices):
        MISSION = "mission", "Mission point (About page)"
        VALUE = "value", "Core value (About page)"
        WHY = "why", "Why choose us (Home page)"
        FOCUS = "focus", "Achievements focus area"

    kind = models.CharField(max_length=10, choices=Kind.choices, db_index=True)
    title = models.CharField(max_length=160)
    text = models.CharField(max_length=300, blank=True, help_text="Optional description (not used for mission points / why-choose-us).")
    icon = models.CharField(max_length=40, blank=True, default="bi-check2-circle", help_text="Bootstrap Icons class, e.g. bi-bullseye.")
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "order", "id"]
        verbose_name = "page list item"
        verbose_name_plural = "page list items"

    def __str__(self):
        return f"{self.get_kind_display()}: {self.title}"


def validate_link(value):
    from django.core.exceptions import ValidationError

    if not (value.startswith("/") or value.startswith("https://") or value.startswith("http://")):
        raise ValidationError("Use a site path such as /programs/ or a full link starting with https://")


class HeroSlide(TimeStamped):
    """A slide in the homepage carousel. If none are published, the plain hero from Site settings is used."""

    eyebrow = models.CharField(max_length=80, blank=True)
    headline = models.CharField(max_length=80, help_text="First part of the headline.")
    headline_accent = models.CharField("Headline (gold part)", max_length=60, blank=True)
    text = models.CharField(max_length=240, blank=True, help_text="Supporting sentence under the headline.")
    image = models.ImageField(
        upload_to="hero/", blank=True, validators=[validate_image_upload],
        help_text="Wide landscape image (1800 x 900 or larger). Keep the main subject on the right half; text sits on the left.",
    )
    image_alt = models.CharField(max_length=200, blank=True)
    primary_label = models.CharField("Primary button text", max_length=40, blank=True)
    primary_link = models.CharField("Primary button link", max_length=200, blank=True, validators=[validate_link], help_text="e.g. /admission/")
    secondary_label = models.CharField("Secondary button text", max_length=40, blank=True)
    secondary_link = models.CharField("Secondary button link", max_length=200, blank=True, validators=[validate_link])
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "homepage slide"
        verbose_name_plural = "homepage carousel slides"

    def __str__(self):
        return f"{self.headline} {self.headline_accent}".strip()

    def save(self, *args, **kwargs):
        optimise_image(self.image, max_side=2200)
        super().save(*args, **kwargs)


class Announcement(TimeStamped):
    """A slim notice bar above the header, e.g. 'Admissions open'. The newest published one is shown."""

    text = models.CharField(max_length=200)
    link_label = models.CharField(max_length=40, blank=True)
    link = models.CharField(max_length=200, blank=True, validators=[validate_link], help_text="e.g. /admission/")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:60]


class Testimonial(TimeStamped):
    """Real feedback supplied by a parent or trainee. Nothing is shown until you add and publish entries."""

    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True, help_text="e.g. Parent of a junior shooter")
    quote = models.TextField(max_length=600)
    photo = models.ImageField(upload_to="testimonials/", blank=True, validators=[validate_image_upload])
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False, help_text="Tick only once the person has agreed to the quote being shown.")

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        optimise_image(self.photo, max_side=600)
        super().save(*args, **kwargs)


class Faq(TimeStamped):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class InstagramReel(TimeStamped):
    """An Instagram reel/video shown as a clickable thumbnail that opens that exact reel on Instagram.

    No thumbnail or URL is ever generated automatically: staff add the real reel link and its thumbnail image.
    """

    title = models.CharField(max_length=120, help_text="Short caption, also used for screen readers.")
    url = models.URLField(
        "Reel link", max_length=300, validators=[validate_instagram_post_url],
        help_text="Open the reel on Instagram, copy its link, e.g. https://www.instagram.com/reel/XXXXXXXXXXX/",
    )
    thumbnail = models.ImageField(
        upload_to="reels/", validators=[validate_image_upload],
        help_text="The reel's cover image (vertical 9:16 works best). Save it from Instagram or use a screenshot of the reel.",
    )
    thumbnail_alt = models.CharField(max_length=200, blank=True, help_text="Describe the cover image. Leave blank to use the title.")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Instagram reel"
        verbose_name_plural = "Instagram reels"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        optimise_image(self.thumbnail, max_side=900)
        super().save(*args, **kwargs)


class MenuItem(TimeStamped):
    """One entry of the website header menu. Only its *visibility* is controlled here.

    Hiding an item never deletes or disables the page behind it: the URL keeps working and all content stays intact.
    """

    key = models.SlugField(unique=True, editable=False)
    label = models.CharField(max_length=60)
    url_name = models.CharField(max_length=60, editable=False, help_text="Internal URL name this item points to.")
    is_cta = models.BooleanField("Shown as the highlighted button", default=False, editable=False)
    order = models.PositiveIntegerField(default=0, editable=False)
    is_visible = models.BooleanField(
        "Show in header menu", default=True,
        help_text="Untick to hide this item from the header (and the footer links). The page itself is not removed.",
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "header menu item"
        verbose_name_plural = "header menu"

    def __str__(self):
        return self.label
