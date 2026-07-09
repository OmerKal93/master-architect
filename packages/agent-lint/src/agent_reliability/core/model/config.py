"""Minimal project configuration: ``.agent-reliability.yaml``.

Only two keys are recognized: ``exclude`` and ``rules``. This is deliberate, not an oversight —
see ``PLAN.md`` trust boundary TB7: config read from a *scanned* repository (which may be
untrusted) must never be able to widen permissions, enable network access, or load plugins. The
enforcement mechanism here is the simplest possible one: those keys do not exist in the schema
at all, so there is nothing dangerous to parse. Any key this loader doesn't recognize produces a
``Diagnostic`` warning rather than being silently accepted — that is what keeps a future,
legitimate schema expansion from quietly becoming a security regression (an attacker-controlled
config with an ``egress: allow`` key today is simply unknown-and-warned, not "ignored and
forgotten").

Only ``yaml.safe_load`` is used, never the full ``yaml.load`` — this repository's config parser
cannot construct arbitrary Python objects from YAML tags (T5/T10 posture).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agent_reliability.core.model.ir import Diagnostic, DiagnosticLevel

CONFIG_FILENAME = ".agent-reliability.yaml"

_KNOWN_TOP_LEVEL_KEYS = {"exclude", "rules"}
_KNOWN_RULES_KEYS = {"enable", "disable"}


@dataclass(frozen=True, slots=True)
class RulesConfig:
    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Config:
    exclude: tuple[str, ...] = ()
    rules: RulesConfig = field(default_factory=RulesConfig)
    diagnostics: tuple[Diagnostic, ...] = ()
    """Warnings collected while loading this config, e.g. unknown keys. Surfaced by the CLI
    rather than discarded."""


def default_config() -> Config:
    return Config()


def _as_str_tuple(value: Any, *, field_name: str, diagnostics: list[Diagnostic]) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    diagnostics.append(
        Diagnostic(
            level=DiagnosticLevel.WARNING,
            message=f"config key {field_name!r} must be a list of strings; ignoring it",
        )
    )
    return ()


def parse_config(raw_text: str) -> Config:
    """Parse config file contents already read from disk. Never touches the filesystem itself."""
    diagnostics: list[Diagnostic] = []
    data = yaml.safe_load(raw_text)

    if data is None:
        return Config(diagnostics=())
    if not isinstance(data, dict):
        diagnostics.append(
            Diagnostic(
                level=DiagnosticLevel.WARNING,
                message=(
                    f"{CONFIG_FILENAME} must contain a YAML mapping at the top level; "
                    "ignoring its contents"
                ),
            )
        )
        return Config(diagnostics=tuple(diagnostics))

    for key in data:
        if key not in _KNOWN_TOP_LEVEL_KEYS:
            diagnostics.append(
                Diagnostic(
                    level=DiagnosticLevel.WARNING,
                    message=(
                        f"unknown config key {key!r} in {CONFIG_FILENAME}; ignoring it "
                        "(this key has no effect — it is not silently trusted)"
                    ),
                )
            )

    exclude = _as_str_tuple(data.get("exclude"), field_name="exclude", diagnostics=diagnostics)

    rules_raw = data.get("rules")
    rules = RulesConfig()
    if rules_raw is not None:
        if isinstance(rules_raw, dict):
            for key in rules_raw:
                if key not in _KNOWN_RULES_KEYS:
                    diagnostics.append(
                        Diagnostic(
                            level=DiagnosticLevel.WARNING,
                            message=(
                                f"unknown config key 'rules.{key}' in {CONFIG_FILENAME}; "
                                "ignoring it"
                            ),
                        )
                    )
            enable = _as_str_tuple(
                rules_raw.get("enable"), field_name="rules.enable", diagnostics=diagnostics
            )
            disable = _as_str_tuple(
                rules_raw.get("disable"), field_name="rules.disable", diagnostics=diagnostics
            )
            rules = RulesConfig(enable=enable, disable=disable)
        else:
            diagnostics.append(
                Diagnostic(
                    level=DiagnosticLevel.WARNING,
                    message=(
                        f"config key 'rules' must be a mapping in {CONFIG_FILENAME}; ignoring it"
                    ),
                )
            )

    return Config(exclude=exclude, rules=rules, diagnostics=tuple(diagnostics))


def load_config_for_root(root: Path) -> Config:
    """Load ``.agent-reliability.yaml`` from ``root`` if present, else return defaults."""
    config_path = root / CONFIG_FILENAME
    if not config_path.is_file():
        return default_config()
    raw_text = config_path.read_text(encoding="utf-8")
    return parse_config(raw_text)
