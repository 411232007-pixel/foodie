import pytest

from foodie.config import ConfigError, load_config


def write_env(path, **values):
    base = {"DISCORD_TOKEN": "abc.def.ghi", "CHANNEL_ID": "123456789012345678", "CLAUDE_MODEL": "haiku", "DATA_DIR": "./data"}
    base.update(values)
    path.write_text("\n".join(f"{k}={v}" for k, v in base.items() if v is not None) + "\n", encoding="utf-8")
    return path


def test_valid_settings(tmp_path):
    cfg = load_config(write_env(tmp_path / ".env"))
    assert cfg.channel_id == 123456789012345678
    assert cfg.claude_model == "haiku"
    assert cfg.data_dir.is_absolute() and cfg.data_dir.name == "data"
    assert "abc.def.ghi" not in repr(cfg)  # the token never shows up in a printed Config


def test_absolute_data_dir_is_kept(tmp_path):
    cfg = load_config(write_env(tmp_path / ".env", DATA_DIR=str(tmp_path / "elsewhere")))
    assert cfg.data_dir == (tmp_path / "elsewhere").resolve()


def test_missing_env_file(tmp_path):
    with pytest.raises(ConfigError, match=".env"):
        load_config(tmp_path / ".env")


@pytest.mark.parametrize("key", ["DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR"])
def test_each_missing_setting_is_named(tmp_path, key):
    with pytest.raises(ConfigError, match=key):
        load_config(write_env(tmp_path / ".env", **{key: None}))


def test_example_text_is_rejected(tmp_path):
    with pytest.raises(ConfigError, match="DISCORD_TOKEN"):
        load_config(write_env(tmp_path / ".env", DISCORD_TOKEN="你的bot_token"))


def test_channel_id_must_be_digits(tmp_path):
    with pytest.raises(ConfigError, match="CHANNEL_ID"):
        load_config(write_env(tmp_path / ".env", CHANNEL_ID="food-log"))


def test_error_message_never_contains_the_token(tmp_path):
    with pytest.raises(ConfigError) as info:
        load_config(write_env(tmp_path / ".env", DISCORD_TOKEN="SECRET-TOKEN-VALUE", CHANNEL_ID="oops"))
    assert "SECRET-TOKEN-VALUE" not in str(info.value)
