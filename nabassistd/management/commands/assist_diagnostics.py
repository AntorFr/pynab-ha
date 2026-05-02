import asyncio
from dataclasses import replace

from django.core.management.base import BaseCommand, CommandError

from nabassistd.config import AssistConfig
from nabassistd.diagnostics import overall_ok, run_diagnostics


class Command(BaseCommand):
    help = "Check Assist Satellite configuration and Wyoming connectivity"

    def add_arguments(self, parser):
        parser.add_argument("--host", type=str)
        parser.add_argument("--port", type=int)
        parser.add_argument("--timeout", type=float, default=2.0)

    def handle(self, *args, **options):
        config = AssistConfig.load()
        if options["host"]:
            config = replace(config, wyoming_host=options["host"])
        if options["port"]:
            config = replace(config, wyoming_port=options["port"])

        results = asyncio.run(
            run_diagnostics(config, timeout=options["timeout"])
        )
        for result in results:
            style = self.style.SUCCESS if result.ok else self.style.ERROR
            status = "OK" if result.ok else "FAIL"
            self.stdout.write(
                style(f"{status} {result.name}: {result.message}")
            )

        if not overall_ok(results):
            raise CommandError("Assist diagnostics failed")
