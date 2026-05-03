from django.shortcuts import render
from django.views.generic import TemplateView

from .models import Config
from .nabhomeassistantd import NabHomeAssistantd


class SettingsView(TemplateView):
    template_name = "nabhomeassistantd/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = Config.load()
        return context

    def post(self, request, *args, **kwargs):
        config = Config.load()
        config.enabled = "enabled" in request.POST
        config.mqtt_host = request.POST.get("mqtt_host", config.mqtt_host)
        config.mqtt_port = int(
            request.POST.get("mqtt_port", config.mqtt_port)
        )
        config.mqtt_username = request.POST.get(
            "mqtt_username", config.mqtt_username
        )
        password = request.POST.get("mqtt_password", "")
        if password:
            config.mqtt_password = password
        config.device_name = request.POST.get(
            "device_name", config.device_name
        )
        config.discovery_prefix = request.POST.get(
            "discovery_prefix", config.discovery_prefix
        )
        config.topic_prefix = request.POST.get(
            "topic_prefix", config.topic_prefix
        )
        config.full_clean()
        config.save()
        NabHomeAssistantd.signal_daemon()
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context=context)
