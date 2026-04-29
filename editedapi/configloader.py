import configparser
import os

DEFAULTS = {
    "api": {
        "log_level": "INFO",
    }
}

# Locate the config file relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.ini')

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(
        f"Config file not found at {CONFIG_PATH}\n"
        f"Please ensure config.ini exists in the project root directory."
    )

# Initialize configparser with defaults
config = configparser.ConfigParser()
config.read_dict(DEFAULTS)

files_read = config.read(CONFIG_PATH)
if not files_read:
    raise IOError(f"Failed to read config file at {CONFIG_PATH}")

# Access helper
def get(section: str, option: str, default: str | None = None) -> str:
    try:
        if default is None:
            return config.get(section, option)
        return config.get(section, option, fallback=default)
    except configparser.NoSectionError:
        raise configparser.NoSectionError(
            f"Section '[{section}]' not found in {CONFIG_PATH}"
        )
    except configparser.NoOptionError:
        raise configparser.NoOptionError(
            option, section
        )
