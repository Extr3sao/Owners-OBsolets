from app.config.settings import load_rules_config


def test_load_rules_config_fallback_json():
    cfg = load_rules_config(yaml_path="non_existent_rules.yaml")
    assert cfg["version"] == "1.0.0"
    assert "thresholds" in cfg
