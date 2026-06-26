from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.http import JsonResponse


from .models import (
    Watch,
    WatchParameter,
    MatchSnapshot,
    TeamStatistic,
    Alert,
)

from .forms import (
    WatchForm,
    WatchParameterFormSet,
)
from .team_analysis import (
    analyse_match,
)


# ==========================================================
# DASHBOARD
# ==========================================================

def dashboard(request):
    active_watches = (
        Watch.objects
        .filter(active=True)
        .order_by("-created_at")
    )

    recent_alerts = (
        Alert.objects
        .select_related("watch")
        .order_by("-created_at")[:10]
    )

    context = {
        "active_watches": active_watches,
        "recent_alerts": recent_alerts,
        "watch_count": Watch.objects.count(),
        "active_watch_count": active_watches.count(),
        "alert_count": Alert.objects.count(),
        "snapshot_count": MatchSnapshot.objects.count(),
    }

    return render(
        request,
        "monitoring/dashboard.html",
        context,
    )


# ==========================================================
# WATCHES
# ==========================================================

class WatchListView(ListView):
    model = Watch
    template_name = "monitoring/watch_list.html"
    context_object_name = "watches"
    ordering = ["-created_at"]


class WatchDetailView(DetailView):
    model = Watch
    template_name = "monitoring/watch_detail.html"
    context_object_name = "watch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        watch = self.object

        context["parameters"] = (
            watch.parameters.all()
        )

        context["latest_snapshot"] = (
            MatchSnapshot.objects
            .filter(watch=watch)
            .order_by("-created_at")
            .first()
        )

        context["recent_alerts"] = (
            Alert.objects
            .filter(watch=watch)
            .order_by("-created_at")[:20]
        )

        context["team_statistics"] = (
            TeamStatistic.objects
            .filter(watch=watch)
            .order_by("-created_at")
        )

        return context


# ==========================================================
# CREATE WATCH
# ==========================================================

class WatchCreateView(CreateView):
    model = Watch
    form_class = WatchForm
    template_name = "monitoring/watch_form.html"
    success_url = reverse_lazy("watch-list")

    def get(self, request, *args, **kwargs):

        form = WatchForm()

        formset = WatchParameterFormSet()

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
            },
        )

    def post(self, request, *args, **kwargs):

        form = WatchForm(request.POST)

        if form.is_valid():

            watch = form.save()

            formset = WatchParameterFormSet(
                request.POST,
                instance=watch,
            )

            if formset.is_valid():

                formset.save()

                return redirect(
                    self.success_url
                )

        else:

            formset = WatchParameterFormSet(
                request.POST
            )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
            },
        )


# ==========================================================
# UPDATE WATCH
# ==========================================================

class WatchUpdateView(UpdateView):
    model = Watch
    form_class = WatchForm
    template_name = "monitoring/watch_form.html"
    success_url = reverse_lazy("watch-list")

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        form = WatchForm(
            instance=self.object
        )

        formset = WatchParameterFormSet(
            instance=self.object
        )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": self.object,
            },
        )

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        form = WatchForm(
            request.POST,
            instance=self.object,
        )

        formset = WatchParameterFormSet(
            request.POST,
            instance=self.object,
        )

        if (
            form.is_valid()
            and formset.is_valid()
        ):

            watch = form.save()

            formset.instance = watch
            formset.save()

            return redirect(
                self.success_url
            )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": self.object,
            },
        )


# ==========================================================
# DELETE WATCH
# ==========================================================

class WatchDeleteView(DeleteView):
    model = Watch

    template_name = (
        "monitoring/watch_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "watch-list"
    )


# ==========================================================
# TOGGLE WATCH
# ==========================================================

def toggle_watch(request, pk):

    watch = get_object_or_404(
        Watch,
        pk=pk
    )

    watch.active = not watch.active
    watch.save()

    return redirect(
        "watch-detail",
        pk=watch.pk,
    )


# ==========================================================
# SNAPSHOTS
# ==========================================================

def watch_snapshots(request, watch_id):

    watch = get_object_or_404(
        Watch,
        pk=watch_id
    )

    snapshots = (
        MatchSnapshot.objects
        .filter(watch=watch)
        .order_by("-created_at")
    )

    context = {
        "watch": watch,
        "snapshots": snapshots,
    }

    return render(
        request,
        "monitoring/watch_snapshots.html",
        context,
    )


# ==========================================================
# TEAM STATISTICS
# ==========================================================

def watch_statistics(
    request,
    watch_id
):

    watch = get_object_or_404(
        Watch,
        pk=watch_id
    )

    statistics = (
        TeamStatistic.objects
        .filter(watch=watch)
        .order_by("-created_at")
    )

    analysis = analyse_match(
        watch
    )

    context = {

        "watch": watch,

        "statistics": statistics,

        "analysis": analysis,

    }

    return render(
        request,
        "monitoring/watch_statistics.html",
        context,
    )


# ==========================================================
# PARAMETER TREND GRAPH
# ==========================================================

def parameter_trend(
    request,
    watch_id,
    parameter_id
):

    watch = get_object_or_404(
        Watch,
        pk=watch_id
    )

    parameter = get_object_or_404(
        WatchParameter,
        pk=parameter_id,
        watch=watch,
    )

    snapshots = (
        MatchSnapshot.objects
        .filter(watch=watch)
        .order_by("elapsed_seconds")
    )

    context = {
        "watch": watch,
        "parameter": parameter,
        "snapshots": snapshots,
        "baseline": parameter.baseline,
        "upper_threshold": (
            parameter.baseline +
            parameter.threshold
        ),
        "lower_threshold": (
            parameter.baseline -
            parameter.threshold
        ),
    }

    return render(
        request,
        "monitoring/parameter_trend.html",
        context,
    )


# ==========================================================
# ALERTS
# ==========================================================

class AlertListView(ListView):
    model = Alert
    template_name = "monitoring/alert_list.html"
    context_object_name = "alerts"
    ordering = ["-created_at"]


class AlertDetailView(DetailView):
    model = Alert
    template_name = "monitoring/alert_detail.html"
    context_object_name = "alert"


def clear_alerts(request):

    Alert.objects.all().delete()

    return redirect(
        "alert-list"
    )


# ==========================================================
# LIVE MONITOR
# ==========================================================

def live_monitor(request):

    active_watches = (
        Watch.objects
        .filter(active=True)
        .order_by("-created_at")
    )

    latest_snapshots = (
        MatchSnapshot.objects
        .select_related("watch")
        .order_by("-created_at")[:50]
    )

    context = {
        "active_watches": active_watches,
        "latest_snapshots": latest_snapshots,
    }

    return render(
        request,
        "monitoring/live_monitor.html",
        context,
    )


def watch_data(request, watch_id):

    watch = get_object_or_404(
        Watch,
        pk=watch_id
    )

    parameter = watch.parameters.first()

    snapshots = (
        MatchSnapshot.objects
        .filter(watch=watch)
        .order_by("elapsed_seconds")
    )

    return JsonResponse({

        "labels": [
            s.elapsed_seconds
            for s in snapshots
        ],

        "actual_points": [
            s.current_points
            for s in snapshots
        ],

        "expected_points": [
            s.expected_points
            for s in snapshots
        ],

        "deviations": [
            s.live_deviation
            for s in snapshots
        ],

        "baseline": (
            float(parameter.baseline)
            if parameter
            else 0
        ),

        "total_game_seconds": (
            watch.total_game_minutes * 60
        ),

    })