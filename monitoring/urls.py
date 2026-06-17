from django.urls import path

from .views import (
    dashboard,
    live_monitor,
    watch_snapshots,
    watch_statistics,
    toggle_watch,
    clear_alerts,
    WatchListView,
    WatchDetailView,
    WatchCreateView,
    WatchUpdateView,
    WatchDeleteView,
    AlertListView,
    AlertDetailView,
    parameter_trend,
    watch_data,
)

urlpatterns = [

    # Dashboard
    path(
        "",
        dashboard,
        name="dashboard"
    ),

    # Live Monitor
    path(
        "monitor/",
        live_monitor,
        name="live-monitor"
    ),

    # Watches
    path(
        "watches/",
        WatchListView.as_view(),
        name="watch-list"
    ),

    path(
        "watches/create/",
        WatchCreateView.as_view(),
        name="watch-create"
    ),

    path(
        "watches/<int:pk>/",
        WatchDetailView.as_view(),
        name="watch-detail"
    ),

    path(
        "watches/<int:pk>/edit/",
        WatchUpdateView.as_view(),
        name="watch-update"
    ),

    path(
        "watches/<int:pk>/delete/",
        WatchDeleteView.as_view(),
        name="watch-delete"
    ),

    path(
        "watches/<int:pk>/toggle/",
        toggle_watch,
        name="toggle-watch"
    ),

    # Snapshots
    path(
        "watches/<int:watch_id>/snapshots/",
        watch_snapshots,
        name="watch-snapshots"
    ),

    # Statistics
    path(
        "watches/<int:watch_id>/statistics/",
        watch_statistics,
        name="watch-statistics"
    ),

    # Alerts
    path(
        "alerts/",
        AlertListView.as_view(),
        name="alert-list"
    ),

    path(
        "alerts/<int:pk>/",
        AlertDetailView.as_view(),
        name="alert-detail"
    ),

    path(
        "alerts/clear/",
        clear_alerts,
        name="clear-alerts"
    ),

    path(
        "watch/<int:watch_id>/parameter/<int:parameter_id>/trend/",
        parameter_trend,
        name="parameter-trend",
    ),

    path(
        "watch/<int:watch_id>/data/",
        watch_data,
        name="watch-data",
    ),
]