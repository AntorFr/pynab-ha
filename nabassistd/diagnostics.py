import importlib.util
from dataclasses import dataclass
from typing import Callable, Iterable

from .client import WyomingAssistClient
from .config import AssistConfig, WakeWordEngineName


@dataclass(frozen=True)
class DiagnosticResult:
    name: str
    ok: bool
    message: str


AssistClientFactory = Callable[[AssistConfig], WyomingAssistClient]


async def run_diagnostics(
    config: AssistConfig,
    client_factory: AssistClientFactory | None = None,
    timeout: float = 2.0,
) -> list[DiagnosticResult]:
    results = [
        DiagnosticResult(
            "assist_enabled",
            config.enabled,
            "Assist is enabled" if config.enabled else "Assist is disabled",
        ),
        _dependency_result(config.wake_word.engine),
    ]

    factory = client_factory or _default_client_factory
    client = factory(config)
    try:
        ping_ok = await client.ping(timeout=timeout)
        results.append(
            DiagnosticResult(
                "wyoming_ping",
                ping_ok,
                "Wyoming pong received"
                if ping_ok
                else "Wyoming did not return the expected pong",
            )
        )
    except Exception as exc:
        results.append(
            DiagnosticResult(
                "wyoming_ping",
                False,
                f"Wyoming ping failed: {exc}",
            )
        )
    finally:
        await client.disconnect()

    return results


def overall_ok(results: Iterable[DiagnosticResult]) -> bool:
    return all(result.ok for result in results)


def _default_client_factory(config: AssistConfig) -> WyomingAssistClient:
    return WyomingAssistClient(
        config.wyoming_host,
        config.wyoming_port,
        config.satellite_name,
    )


def _dependency_result(engine: WakeWordEngineName) -> DiagnosticResult:
    if engine == WakeWordEngineName.MICRO:
        return _module_result("pymicro_wakeword", "pymicro-wakeword")
    if engine == WakeWordEngineName.OPENWAKEWORD:
        return _module_result("openwakeword", "openWakeWord")
    if engine == WakeWordEngineName.REMOTE:
        return DiagnosticResult(
            "wake_word_dependency",
            True,
            "Remote wake-word mode does not require a local engine",
        )
    return DiagnosticResult(
        "wake_word_dependency",
        False,
        f"Unsupported wake-word engine: {engine}",
    )


def _module_result(module_name: str, label: str) -> DiagnosticResult:
    ok = importlib.util.find_spec(module_name) is not None
    return DiagnosticResult(
        "wake_word_dependency",
        ok,
        f"{label} is installed"
        if ok
        else f"{label} is not installed; install requirements-assist.txt",
    )
