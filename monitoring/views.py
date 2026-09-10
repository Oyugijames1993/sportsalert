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
    StatAlertRule,
    StatOccurrence,
    StatAlert,
    StatOddsModel,
)

from . import odds_model

from .forms import (
    WatchForm,
    WatchParameterFormSet,
    StatAlertRuleFormSet,
    StatOddsModelFormSet,
)


from .team_analysis import (
    analyse_match,
    analyse_team,
    get_team_snapshots,
)
from monitoring.services import get_today_live_games

from django.shortcuts import (
    get_object_or_404,
    render,
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

        # ── Football stat-tracking data ────────────────────────────────
        stat_rules = list(watch.stat_alert_rules.all().order_by("stat_type", "mode"))

        # Latest recorded value per (stat_type, team) — for the summary table.
        latest_values = {}
        for occ in watch.stat_occurrences.order_by("stat_type", "team", "detected_at"):
            latest_values[(occ.stat_type, occ.team)] = occ.value_at_time

        stat_summary = []
        seen_stats = set()
        for rule in stat_rules:
            if rule.stat_type in seen_stats:
                continue
            seen_stats.add(rule.stat_type)
            stat_summary.append({
                "stat_type": rule.get_stat_type_display(),
                "stat_type_key": rule.stat_type,
                "home_value": latest_values.get((rule.stat_type, "home"), 0),
                "away_value": latest_values.get((rule.stat_type, "away"), 0),
                "expected_total": rule.expected_total,
            })

        context["stat_rules"] = stat_rules
        context["stat_summary"] = stat_summary
        context["stat_occurrences"] = (
            watch.stat_occurrences.order_by("-detected_at")[:50]
        )
        context["stat_alerts"] = (
            watch.stat_alerts.order_by("-created_at")[:20]
        )

        # ── Live odds boards ────────────────────────────────────────────
        odds_boards = []
        t = watch.elapsed_minutes or 0
        for row in watch.stat_odds_models.all():
            home_val = latest_values.get((row.stat_type, "home"), 0)
            away_val = latest_values.get((row.stat_type, "away"), 0)
            k = home_val + away_val
            try:
                r = odds_model.get_dispersion_r(row.stat_type, row.dispersion_r)
                board = odds_model.odds_board(
                    mu_0=row.mu_0, r=r, t=t, k=k, overround=row.overround
                )
                board["stat_type"] = row.get_stat_type_display()
                board["observed_k"] = k
                odds_boards.append(board)
            except (ValueError, ZeroDivisionError):
                pass

        context["odds_boards"] = odds_boards
        context["elapsed_minutes"] = t

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
        stat_formset = StatAlertRuleFormSet()
        odds_formset = StatOddsModelFormSet()
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "stat_formset": stat_formset,
                "odds_formset": odds_formset,
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
            stat_formset = StatAlertRuleFormSet(
                request.POST,
                instance=watch,
            )
            odds_formset = StatOddsModelFormSet(
                request.POST,
                instance=watch,
            )
            if formset.is_valid() and stat_formset.is_valid() and odds_formset.is_valid():
                formset.save()
                stat_formset.save()
                odds_formset.save()
                return redirect(
                    self.success_url
                )
        else:
            formset = WatchParameterFormSet(
                request.POST
            )
            stat_formset = StatAlertRuleFormSet(
                request.POST
            )
            odds_formset = StatOddsModelFormSet(
                request.POST
            )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "stat_formset": stat_formset,
                "odds_formset": odds_formset,
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
        stat_formset = StatAlertRuleFormSet(
            instance=self.object
        )
        odds_formset = StatOddsModelFormSet(
            instance=self.object
        )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "stat_formset": stat_formset,
                "odds_formset": odds_formset,
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
        stat_formset = StatAlertRuleFormSet(
            request.POST,
            instance=self.object,
        )
        odds_formset = StatOddsModelFormSet(
            request.POST,
            instance=self.object,
        )
        if (
            form.is_valid()
            and formset.is_valid()
            and stat_formset.is_valid()
            and odds_formset.is_valid()
        ):
            watch = form.save()
            formset.instance = watch
            formset.save()
            stat_formset.instance = watch
            stat_formset.save()
            odds_formset.instance = watch
            odds_formset.save()
            return redirect(
                self.success_url
            )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "stat_formset": stat_formset,
                "odds_formset": odds_formset,
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




def team_analysis(
    request,
    watch_id,
):

    watch = get_object_or_404(
        Watch,
        pk=watch_id
    )

    teams = list(

        TeamStatistic.objects

        .filter(
            watch=watch
        )

        .values(
            "team_id",
            "team_name"
        )

        .distinct()

    )

    if len(teams) < 2:

        return render(

            request,

            "monitoring/team_analysis.html",

            {
                "watch": watch,
                "error": (
                    "No team statistics "
                    "available yet."
                ),
            },

        )

    home_team = teams[0]
    away_team = teams[1]

    home_analysis = analyse_team(
        watch,
        home_team["team_id"]
    )

    away_analysis = analyse_team(
        watch,
        away_team["team_id"]
    )

    home_snapshots = get_team_snapshots(
        watch,
        home_team["team_id"]
    )

    away_snapshots = get_team_snapshots(
        watch,
        away_team["team_id"]
    )

    # ======================================
    # HOME TEAM GRAPH DATA
    # ======================================

    home_labels = []

    home_three_pa = []
    home_three_pm = []

    home_two_pa = []
    home_two_pm = []

    for stat in home_snapshots:

        home_labels.append(
            stat.elapsed_seconds
        )

        home_three_pa.append(
            stat.three_pt_attempted
        )

        home_three_pm.append(
            stat.three_pt_made
        )

        home_two_pa.append(
            stat.two_pt_attempted
        )

        home_two_pm.append(
            stat.two_pt_made
        )

    # ======================================
    # AWAY TEAM GRAPH DATA
    # ======================================

    away_labels = []

    away_three_pa = []
    away_three_pm = []

    away_two_pa = []
    away_two_pm = []

    for stat in away_snapshots:

        away_labels.append(
            stat.elapsed_seconds
        )

        away_three_pa.append(
            stat.three_pt_attempted
        )

        away_three_pm.append(
            stat.three_pt_made
        )

        away_two_pa.append(
            stat.two_pt_attempted
        )

        away_two_pm.append(
            stat.two_pt_made
        )

    context = {

        "watch": watch,

        "home_team": home_team,
        "away_team": away_team,

        "home_analysis": home_analysis,
        "away_analysis": away_analysis,

        "home_snapshots": home_snapshots,
        "away_snapshots": away_snapshots,

        "home_labels": home_labels,
        "home_three_pa": home_three_pa,
        "home_three_pm": home_three_pm,
        "home_two_pa": home_two_pa,
        "home_two_pm": home_two_pm,

        "away_labels": away_labels,
        "away_three_pa": away_three_pa,
        "away_three_pm": away_three_pm,
        "away_two_pa": away_two_pa,
        "away_two_pm": away_two_pm,

    }

    return render(

        request,

        "monitoring/team_analysis.html",

        context,

    )


def live_games(request):

    games = get_today_live_games()

    return render(
        request,
        "monitoring/live_games.html",
        {
            "games": games,
        },
    )

# ==========================================================
# FOOTBALL STAT TREND (home / away / total time series)
# ==========================================================

def football_stat_trend(request, watch_id, stat_type):
    watch = get_object_or_404(Watch, pk=watch_id)
    stat_label = dict(StatAlertRule.STAT_TYPE_CHOICES).get(stat_type, stat_type)

    return render(
        request,
        "monitoring/football_stat_trend.html",
        {
            "watch": watch,
            "stat_type": stat_type,
            "stat_label": stat_label,
        },
    )


def football_stat_data(request, watch_id, stat_type):
    watch = get_object_or_404(Watch, pk=watch_id)

    occurrences = list(
        StatOccurrence.objects
        .filter(watch=watch, stat_type=stat_type)
        .order_by("detected_at")
    )

    anchor = watch.monitoring_start or watch.created_at

    home_series = []
    away_series = []
    total_series = []

    latest_home = 0
    latest_away = 0

    for occ in occurrences:
        minutes_elapsed = round((occ.detected_at - anchor).total_seconds() / 60, 1)

        if occ.team == "home":
            latest_home = occ.value_at_time
        else:
            latest_away = occ.value_at_time

        point = {"x": minutes_elapsed, "y": occ.value_at_time}
        if occ.team == "home":
            home_series.append(point)
        else:
            away_series.append(point)

        total_series.append({"x": minutes_elapsed, "y": latest_home + latest_away})

    # Flat reference line at the user's own expected total, spanning the
    # same time range as the actual data collected so far.
    rule_with_expected = (
        watch.stat_alert_rules
        .filter(stat_type=stat_type, expected_total__isnull=False)
        .first()
    )
    expected_total = rule_with_expected.expected_total if rule_with_expected else None
    expected_series = []
    if expected_total is not None and total_series:
        min_x = min(p["x"] for p in total_series)
        max_x = max(p["x"] for p in total_series)
        expected_series = [
            {"x": min_x, "y": expected_total},
            {"x": max_x, "y": expected_total},
        ]

    return JsonResponse({
        "home": home_series,
        "away": away_series,
        "total": total_series,
        "expected": expected_series,
        "expected_total": expected_total,
        "home_team": watch.home_team,
        "away_team": watch.away_team,
    })
