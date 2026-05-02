from django.urls import path

from .views import DiagnosticsView, SettingsView

urlpatterns = [
    path("settings", SettingsView.as_view()),
    path("diagnostics", DiagnosticsView.as_view()),
]
