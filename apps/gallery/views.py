from django.shortcuts import render

from apps.core.utils import page_enabled, paginate

from apps.core.models import InstagramReel

from .models import Category, GalleryImage

PER_PAGE = 12


@page_enabled("show_gallery")
def gallery_index(request):
    images = GalleryImage.objects.filter(is_published=True).select_related("category")
    used = set(images.values_list("category_id", flat=True))
    categories = [c for c in Category.objects.all() if c.pk in used]
    active = next((c for c in categories if c.slug == request.GET.get("category")), None)
    if active:
        images = images.filter(category=active)
    page = paginate(request, images, PER_PAGE)
    return render(request, "gallery/index.html", {
        "page_obj": page,
        "images": page.object_list,
        "categories": categories,
        "active_category": active,
        "reels": InstagramReel.objects.filter(is_published=True)[:12],
        "meta_description": "Photo gallery of training, events and the range at Rudra Sports Rifle Shooting Society, Indore.",
    })
