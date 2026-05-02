import asyncio

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from .config import AssistConfig, WakeWordConfig, WakeWordEngineName
from .diagnostics import run_diagnostics
from .models import Config
from .nabassistd import NabAssistd


class SettingsView(TemplateView):
    template_name = "nabassistd/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = Config.load()
        context["wake_word_engines"] = Config.WAKE_WORD_ENGINE_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        config = Config.load()
        config.enabled = "enabled" in request.POST
        if "satellite_name" in request.POST:
            config.satellite_name = request.POST["satellite_name"]
        if "wyoming_host" in request.POST:
            config.wyoming_host = request.POST["wyoming_host"]
        if "wyoming_port" in request.POST:
            config.wyoming_port = int(request.POST["wyoming_port"])
        if "wake_word_engine" in request.POST:
            config.wake_word_engine = request.POST["wake_word_engine"]
        if "wake_word_model" in request.POST:
            config.wake_word_model = request.POST["wake_word_model"]
        if "wake_word_sensitivity" in request.POST:
            config.wake_word_sensitivity = float(
                request.POST["wake_word_sensitivity"]
            )
        if "pre_roll_seconds" in request.POST:
            config.pre_roll_seconds = float(request.POST["pre_roll_seconds"])
        config.fallback_to_remote = "fallback_to_remote" in request.POST
        config.full_clean()
        config.save()
        NabAssistd.signal_daemon()
        context = self.get_context_data(**kwargs)
        return render(request, SettingsView.template_name, context=context)


class DiagnosticsView(TemplateView):
    def post(self, request, *args, **kwargs):
        config = _assist_config_from_post(request.POST)
        results = asyncio.run(run_diagnostics(config))
        return JsonResponse(
            {
                "results": [
                    {
                        "name": result.name,
                        "ok": result.ok,
                        "message": result.message,
                    }
                    for result in results
                ]
            }
        )


def _assist_config_from_post(post) -> AssistConfig:
    record = Config.load()
    return AssistConfig(
        enabled="enabled" in post,
        satellite_name=post.get("satellite_name", record.satellite_name),
        wyoming_host=post.get("wyoming_host", record.wyoming_host),
        wyoming_port=int(post.get("wyoming_port", record.wyoming_port)),
        wake_word=WakeWordConfig(
            engine=WakeWordEngineName(
                post.get("wake_word_engine", record.wake_word_engine)
            ),
            model=post.get("wake_word_model", record.wake_word_model),
            sensitivity=float(
                post.get(
                    "wake_word_sensitivity", record.wake_word_sensitivity
                )
            ),
            pre_roll_seconds=float(
                post.get("pre_roll_seconds", record.pre_roll_seconds)
            ),
            fallback_to_remote="fallback_to_remote" in post,
        ),
    )
