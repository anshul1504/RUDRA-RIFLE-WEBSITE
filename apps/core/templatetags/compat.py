"""Compatibility template filters, loaded as builtins (see TEMPLATES in settings).

Django 5.1 removed the `length_is` filter that django-jazzmin 3.0's admin templates still use.
"""
from django import template

register = template.Library()


@register.filter(is_safe=False)
def length_is(value, arg):
    """Return True if the value's length equals `arg` (old Django behaviour)."""
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return ""
