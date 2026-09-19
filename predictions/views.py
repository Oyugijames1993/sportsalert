from django.shortcuts import get_object_or_404, redirect, render

from .forms import CoachProfileForm
from .models import CoachProfile
from .services import simulate_match


def coach_list(request):
    coaches = CoachProfile.objects.all().order_by("coach_name")

    return render(
        request,
        "predictions/coach_list.html",
        {"coaches": coaches},
    )


def coach_create(request):

    if request.method == "POST":
        form = CoachProfileForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("coach_list")

    else:
        form = CoachProfileForm()

    return render(
        request,
        "predictions/coach_form.html",
        {
            "form": form,
            "title": "Create Coach Profile",
        },
    )


def coach_edit(request, pk):

    coach = get_object_or_404(
        CoachProfile,
        pk=pk,
    )

    if request.method == "POST":
        form = CoachProfileForm(
            request.POST,
            instance=coach,
        )

        if form.is_valid():
            form.save()
            return redirect("coach_list")

    else:
        form = CoachProfileForm(
            instance=coach,
        )

    return render(
        request,
        "predictions/coach_form.html",
        {
            "form": form,
            "title": f"Edit {coach.coach_name}",
            "coach": coach,
        },
    )


def coach_delete(request, pk):

    coach = get_object_or_404(
        CoachProfile,
        pk=pk,
    )

    if request.method == "POST":
        coach.delete()
        return redirect("coach_list")

    return render(
        request,
        "predictions/coach_delete.html",
        {"coach": coach},
    )


def simulate(request):

    coaches = CoachProfile.objects.all().order_by("coach_name")

    result = None

    if request.method == "POST":

        home_coach_id = request.POST.get(
            "home_coach"
        )

        away_coach_id = request.POST.get(
            "away_coach"
        )

        simulations = int(
            request.POST.get(
                "simulations",
                100000,
            )
        )

        home_coach = get_object_or_404(
            CoachProfile,
            pk=home_coach_id,
        )

        away_coach = get_object_or_404(
            CoachProfile,
            pk=away_coach_id,
        )

        result = simulate_match(
            home_coach,
            away_coach,
            simulations=simulations,
        )

    return render(
        request,
        "predictions/simulate.html",
        {
            "coaches": coaches,
            "result": result,
        },
    )
