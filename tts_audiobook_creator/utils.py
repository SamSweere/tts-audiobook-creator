import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)


def get_project_root_path() -> Path:
    return Path(__file__).parent.parent


def load_config() -> dict[str, str | dict | list]:
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    # Update all `{path_to_project_root}` with the actual path to the project root
    project_root_path = get_project_root_path()
    for key, value in config.items():
        if isinstance(value, str):
            config[key] = value.replace("{path_to_project_root}", str(project_root_path))
            logger.debug(f"Updated {key} to {config[key]}")
        elif isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, str):
                    config[key][k] = v.replace("{path_to_project_root}", str(project_root_path))
                    logger.debug(f"Updated {key}.{k} to {config[key][k]}")

    return config
