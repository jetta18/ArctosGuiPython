# File: utils/settings_manager.py

import os
import yaml

# ✅ Define config path relative to project root (src/config/user_config.yaml)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'user_config.yaml')

# Default settings if the config file doesn't exist yet
DEFAULT_SETTINGS = {
    "theme": "Light",
    "language": "English",
    "ui_color_theme": "Blue",
    "max_fps": 30,
    "auto_update_saved_poses": False,
    "joint_directions": {i: 1 for i in range(6)}  # Default direction for all joints
}

class SettingsManager:
    """
    SettingsManager provides centralized loading, accessing, and updating of application-wide settings.
    All settings are stored in a YAML file and persist across sessions.
    """
    def __init__(self):
        if not os.path.exists(CONFIG_PATH):
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
        else:
            with open(CONFIG_PATH, 'r') as f:
                self.settings = yaml.safe_load(f) or DEFAULT_SETTINGS.copy()

    def save(self):
        """Save current settings to the YAML file."""
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(self.settings, f)

    def get(self, key, default=None):
        """
        Retrieve a setting value by key.

        :param key: The setting key to fetch
        :param default: Optional default value to return if key is not set
        :return: The current value or default if not set
        """
        return self.settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        """
        Update a setting value and save it.

        :param key: The setting key to update
        :param value: The new value to store
        """
        self.settings[key] = value
        self.save()

    def all(self):
        """
        Return a dictionary of all settings.

        :return: dict of current settings
        """
        return self.settings