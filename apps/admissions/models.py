from django.db import models

from apps.core.models import TimeStamped


class AdmissionEnquiry(TimeStamped):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CLOSED = "closed", "Closed"

    class ContactMethod(models.TextChoices):
        PHONE = "phone", "Phone call"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        NO_ANSWER = "no_answer", "Prefer not to say"

    class Experience(models.TextChoices):
        BEGINNER = "beginner", "Beginner \u2014 No Previous Experience"
        INTERMEDIATE = "intermediate", "Intermediate \u2014 Some Shooting Experience"
        ADVANCED = "advanced", "Advanced \u2014 Experienced Shooter"

    class ShootingInterest(models.TextChoices):
        AIR_RIFLE = "10m_air_rifle", "10M Air Rifle"
        AIR_PISTOL = "10m_air_pistol", "10M Air Pistol"
        NOT_SURE = "not_sure", "Not sure yet"

    class PreferredTime(models.TextChoices):
        MORNING = "morning", "Morning"
        EVENING = "evening", "Evening"
        WEEKEND = "weekend", "Weekends"
        FLEXIBLE = "flexible", "Flexible / any time"

    class HowHeard(models.TextChoices):
        FRIENDS = "friends", "Friend or family"
        SOCIAL = "social", "Social media"
        NEWS = "news", "Newspaper / news"
        SCHOOL = "school", "School or college"
        VISIT = "visit", "Visited the academy"
        OTHER = "other", "Other"

    applicant_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    city = models.CharField("City / area", max_length=80, blank=True)
    institution = models.CharField("School / college & class (if studying)", max_length=160, blank=True)
    guardian_name = models.CharField("Parent / guardian name", max_length=120, blank=True)
    guardian_mobile = models.CharField("Parent / guardian mobile", max_length=15, blank=True)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    program = models.ForeignKey(
        "programs.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="enquiries",
        verbose_name="Program of interest",
    )
    shooting_interest = models.CharField("Type of shooting", max_length=20, choices=ShootingInterest.choices, blank=True)
    experience_level = models.CharField("Previous shooting experience", max_length=15, choices=Experience.choices, blank=True)
    preferred_time = models.CharField("Preferred training time", max_length=10, choices=PreferredTime.choices, blank=True)
    how_heard = models.CharField("How did you hear about us?", max_length=10, choices=HowHeard.choices, blank=True)
    preferred_contact = models.CharField(max_length=10, choices=ContactMethod.choices, default=ContactMethod.PHONE)
    message = models.TextField(blank=True)
    consent = models.BooleanField(default=False)
    consent_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW, db_index=True)
    staff_notes = models.TextField(blank=True, help_text="Internal notes. Never shown to the applicant.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "admission enquiry"
        verbose_name_plural = "admission enquiries"

    def __str__(self):
        return f"{self.applicant_name} ({self.get_status_display()})"
