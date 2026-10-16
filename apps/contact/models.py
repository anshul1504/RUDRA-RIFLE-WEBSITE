from django.db import models

from apps.core.models import TimeStamped


class ContactMessage(TimeStamped):
    class Status(models.TextChoices):
        NEW = "new", "New"
        REPLIED = "replied", "Replied"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=160)
    message = models.TextField()
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    staff_notes = models.TextField(blank=True, help_text="Internal notes. Never shown to the sender.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contact message"
        verbose_name_plural = "contact messages"

    def __str__(self):
        return f"{self.subject} - {self.name}"
