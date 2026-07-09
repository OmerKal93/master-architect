from __future__ import annotations

from pathlib import Path

from agent_reliability.core.model.config import (
    CONFIG_FILENAME,
    default_config,
    load_config_for_root,
    parse_config,
)
from agent_reliability.core.model.ir import DiagnosticLevel


def test_default_config_is_empty() -> None:
    config = default_config()
    assert config.exclude == ()
    assert config.rules.enable == ()
    assert config.rules.disable == ()
    assert config.diagnostics == ()


def test_missing_config_file_returns_default(tmp_path: Path) -> None:
    config = load_config_for_root(tmp_path)
    assert config == default_config()


def test_empty_config_file(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text("", encoding="utf-8")
    config = load_config_for_root(tmp_path)
    assert config.exclude == ()
    assert config.diagnostics == ()


def test_parses_exclude_and_rules() -> None:
    config = parse_config(
        """
        exclude:
          - vendor/
          - "*.generated.py"
        rules:
          enable: [AR001]
          disable: [AR014]
        """
    )
    assert config.exclude == ("vendor/", "*.generated.py")
    assert config.rules.enable == ("AR001",)
    assert config.rules.disable == ("AR014",)
    assert config.diagnostics == ()


def test_unknown_top_level_key_warns_and_is_ignored() -> None:
    # This is the TB7 enforcement test: a scanned repo's config file cannot smuggle in a
    # dangerous key (e.g. "egress", "plugins", "network") because such keys are simply not
    # part of the schema. They must produce a warning, not be silently accepted or trusted.
    config = parse_config(
        """
        exclude: []
        egress: allow
        plugins: ["evil-plugin"]
        """
    )
    assert not hasattr(config, "egress")
    assert not hasattr(config, "plugins")
    messages = [d.message for d in config.diagnostics]
    assert any("egress" in m for m in messages)
    assert any("plugins" in m for m in messages)
    assert all(d.level is DiagnosticLevel.WARNING for d in config.diagnostics)


def test_unknown_rules_subkey_warns() -> None:
    config = parse_config(
        """
        rules:
          enable: [AR001]
          allow_dangerous: true
        """
    )
    messages = [d.message for d in config.diagnostics]
    assert any("rules.allow_dangerous" in m for m in messages)


def test_non_mapping_top_level_warns_and_returns_defaults() -> None:
    config = parse_config("- just\n- a\n- list\n")
    assert config.exclude == ()
    assert len(config.diagnostics) == 1
    assert config.diagnostics[0].level is DiagnosticLevel.WARNING


def test_exclude_must_be_list_of_strings() -> None:
    config = parse_config("exclude: not-a-list\n")
    assert config.exclude == ()
    assert any("exclude" in d.message for d in config.diagnostics)


def test_rules_must_be_a_mapping() -> None:
    config = parse_config("rules: not-a-mapping\n")
    assert config.rules.enable == ()
    assert any("rules" in d.message for d in config.diagnostics)


def test_uses_safe_load_rejects_arbitrary_python_objects() -> None:
    # A classic yaml.load() (FullLoader/UnsafeLoader) footgun: constructing arbitrary Python
    # objects from YAML tags. safe_load must refuse this outright rather than silently execute
    # something. We assert it raises rather than succeeding with an attacker-controlled object.
    import yaml

    malicious_yaml = "exclude: !!python/object/apply:os.system ['echo pwned']"
    try:
        parse_config(malicious_yaml)
    except yaml.YAMLError:
        pass  # safe_load correctly refused the unknown tag — this is the expected outcome.
    else:
        raise AssertionError(
            "parse_config must not silently accept unsafe YAML tags; yaml.safe_load should "
            "have raised for a python/object/apply tag"
        )


def test_real_file_round_trip(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        "exclude: [vendor/]\nrules:\n  disable: [AR014]\n", encoding="utf-8"
    )
    config = load_config_for_root(tmp_path)
    assert config.exclude == ("vendor/",)
    assert config.rules.disable == ("AR014",)
