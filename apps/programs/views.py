from django.shortcuts import get_object_or_404, render

from apps.core.utils import paginate

from .models import Program


def program_list(request):
    page = paginate(request, Program.objects.filter(is_published=True).prefetch_related("highlights"), 6)
    return render(request, "programs/list.html", {
        "page_obj": page,
        "programs": page.object_list,
        "meta_description": "Beginner, advanced competitive and junior rifle and pistol shooting programs at Rudra Sports Rifle Shooting Society, Indore.",
    })


def program_detail(request, slug):
    program = get_object_or_404(Program.objects.prefetch_related("highlights"), slug=slug, is_published=True)
    others = Program.objects.filter(is_published=True).exclude(pk=program.pk)[:2]
    return render(request, "programs/detail.html", {
        "program": program, "others": others, "meta_description": program.summary,
    })
