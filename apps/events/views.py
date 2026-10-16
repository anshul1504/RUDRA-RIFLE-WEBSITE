from django.shortcuts import get_object_or_404, render

from apps.core.utils import page_enabled, paginate

from .models import Event

PER_PAGE = 6


@page_enabled("show_events")
def event_list(request):
    return render(request, "events/list.html", {
        "upcoming_page": paginate(request, Event.objects.upcoming(), PER_PAGE, "upcoming"),
        "past_page": paginate(request, Event.objects.past(), PER_PAGE, "past"),
        "meta_description": "Upcoming and past shooting events and competitions of Rudra Sports Rifle Shooting Society, Indore.",
    })


@page_enabled("show_events")
def event_detail(request, slug):
    event = get_object_or_404(Event.objects.published().prefetch_related("photos"), slug=slug)
    return render(request, "events/detail.html", {"event": event, "meta_description": event.summary or event.title})
