from django.shortcuts import get_object_or_404, render

from apps.core.models import ContentItem
from apps.core.utils import page_enabled, paginate

from .models import Achievement


@page_enabled("show_achievements")
def achievement_list(request):
    return render(request, "achievements/list.html", {
        "page_obj": paginate(request, Achievement.objects.filter(is_published=True), 9),
        "themes": ContentItem.objects.filter(kind=ContentItem.Kind.FOCUS, is_published=True),
        "meta_description": "Achievements and focus areas of Rudra Sports Rifle Shooting Society, Indore.",
    })


@page_enabled("show_achievements")
def achievement_detail(request, slug):
    item = get_object_or_404(Achievement, slug=slug, is_published=True)
    return render(request, "achievements/detail.html", {"item": item, "meta_description": item.summary or item.title})
