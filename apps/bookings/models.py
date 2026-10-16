import secrets
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.core.models import TimeStamped

ACTIVE_STATUSES = ("pending", "confirmed", "attended")  # statuses that occupy a seat


class SlotQuerySet(models.QuerySet):
    def with_booked(self):
        """Annotate each slot with the number of seats taken (cancelled bookings free their seats)."""
        return self.annotate(
            booked=Coalesce(Sum("bookings__participants", filter=Q(bookings__status__in=ACTIVE_STATUSES)), 0)
        ).order_by("date", "start_time")  # Meta.ordering is dropped by aggregate queries

    def open_for_booking(self):
        today = timezone.localdate()
        return self.filter(is_published=True, date__gte=today).select_related("program")


class Slot(TimeStamped):
    """A bookable practice session on a given date and time."""

    program = models.ForeignKey(
        "programs.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="slots",
        limit_choices_to={"allow_booking": True}, help_text="Optional. Only programs with 'Offer slot booking' ticked are listed.",
    )
    title = models.CharField(max_length=120, blank=True, help_text="Optional label, e.g. 'Morning range session'.")
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(500)], help_text="Total seats (shooters) available in this slot.",
    )
    price_note = models.CharField(
        max_length=120, blank=True, help_text="Optional, e.g. the fee for this slot. Shown only if filled in.",
    )
    notes = models.CharField(max_length=240, blank=True, help_text="Shown to visitors, e.g. 'Bring a photo ID'.")
    is_published = models.BooleanField("Open for booking", default=True)

    objects = SlotQuerySet.as_manager()

    class Meta:
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(fields=["date", "start_time", "program"], name="unique_slot_per_program_time"),
        ]

    def __str__(self):
        label = self.title or (self.program.title if self.program_id else "Practice slot")
        return f"{label} - {self.date:%d %b %Y} {self.start_time:%I:%M %p}"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "The end time must be after the start time."})

    @property
    def starts_at(self):
        return timezone.make_aware(datetime.combine(self.date, self.start_time))

    @property
    def is_past(self):
        return self.starts_at <= timezone.now()

    @property
    def booked_count(self):
        if hasattr(self, "booked"):  # annotated queryset
            return self.booked
        return self.bookings.filter(status__in=ACTIVE_STATUSES).aggregate(n=Coalesce(Sum("participants"), 0))["n"]

    @property
    def seats_left(self):
        return max(self.capacity - self.booked_count, 0)

    @property
    def is_full(self):
        return self.seats_left == 0

    @property
    def is_bookable(self):
        return self.is_published and not self.is_past and not self.is_full


class SlotSchedule(TimeStamped):
    """A weekly pattern. Use the 'Generate slots' action to create the actual dated slots."""

    WEEKDAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")]

    program = models.ForeignKey(
        "programs.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="slot_schedules",
        limit_choices_to={"allow_booking": True},
    )
    title = models.CharField(max_length=120, blank=True)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(500)])
    price_note = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name = "weekly slot schedule"
        verbose_name_plural = "weekly slot schedules"

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%I:%M %p}-{self.end_time:%I:%M %p}"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "The end time must be after the start time."})

    def generate(self, days=14):
        """Create missing slots for the next `days` days. Returns the number created."""
        created = 0
        today = timezone.localdate()
        for offset in range(days + 1):
            day = today + timedelta(days=offset)
            if day.weekday() != self.weekday:
                continue
            _, was_created = Slot.objects.get_or_create(
                date=day, start_time=self.start_time, program=self.program,
                defaults={
                    "end_time": self.end_time, "capacity": self.capacity, "title": self.title,
                    "price_note": self.price_note, "is_published": True,
                },
            )
            created += was_created
        return created


def new_reference():
    return "RSB-" + secrets.token_hex(3).upper()


class SlotBooking(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        ATTENDED = "attended", "Attended"
        CANCELLED = "cancelled", "Cancelled"

    class ExperienceLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner \u2014 No Previous Experience"
        INTERMEDIATE = "intermediate", "Intermediate \u2014 Some Shooting Experience"
        ADVANCED = "advanced", "Advanced \u2014 Experienced Shooter"

    class ShootingType(models.TextChoices):
        AIR_RIFLE = "10m_air_rifle", "10M Air Rifle"
        AIR_PISTOL = "10m_air_pistol", "10M Air Pistol"

    reference = models.CharField(max_length=12, unique=True, default=new_reference, editable=False)
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, related_name="bookings")
    name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    participants = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(20)], help_text="Number of shooters in this booking.",
    )
    # Required on the public form; blank=True keeps bookings made before these fields existed valid and untouched.
    experience_level = models.CharField("Previous shooting experience", max_length=15, choices=ExperienceLevel.choices, blank=True)
    shooting_type = models.CharField("Type of shooting", max_length=20, choices=ShootingType.choices, blank=True)
    message = models.CharField(max_length=300, blank=True)
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    staff_notes = models.TextField(blank=True, help_text="Internal notes. Never shown to the visitor.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "slot booking"
        verbose_name_plural = "slot bookings"

    def __str__(self):
        return f"{self.reference} - {self.name}"
