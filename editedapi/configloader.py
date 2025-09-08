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

# Initialize configparser with defaults
config = configparser.ConfigParser()
config.read_dict(DEFAULTS)       # Load defaults first
config.read(CONFIG_PATH)         # Then override from file if present

# Access helper
def get(section, option):
    return config.get(section, option)
