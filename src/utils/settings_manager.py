"""
File: utils/settings_manager.py

This module provides a SettingsManager class that handles the loading, accessing, and
saving of application settings. Settings are stored in a YAML file, which persists across
different application sessions. The module also includes default settings that are used if
the configuration file is not found.
"""

import os
import yaml

# Define the base directory and configuration file path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'user_config.yaml')

# Default settings used when the config file does not exist or is corrupted
DEFAULT_SETTINGS = {
    "theme": "Light",  # Default UI theme
    "language": "English",  # Default language
    "ui_color_theme": "Blue",  # Default color theme for UI elements
    "max_fps": 30,  # Maximum frames per second
    "auto_update_saved_poses": False,  # Whether to auto-update saved poses
    "joint_directions": {i: 1 for i in range(6)}  # Default direction for each joint (1 or -1)
}

class SettingsManager:
    """
    The SettingsManager class provides centralized loading, accessing, and updating
    of application-wide settings. All settings are stored in a YAML file and
    persist across different application sessions.
    """
    def __init__(self):
        """
        Initializes the SettingsManager by loading settings from the YAML file,
        or creating the file with default settings if it doesn't exist.
        """
        if not os.path.exists(CONFIG_PATH):
            # If the config file doesn't exist, use default settings and save them
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
        else:
            # If the config file exists, try to load settings from it
            with open(CONFIG_PATH, 'r') as f:
                loaded_settings = yaml.safe_load(f)
                # Use default settings if the file is empty or corrupted
                self.settings = loaded_settings or DEFAULT_SETTINGS.copy()

    def save(self):
        """
        Saves the current settings to the YAML configuration file.
        """
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(self.settings, f)

    def get(self, key, default=None):
        """
        Retrieves a setting value by its key. If the key is not found in the
        current settings, it returns a provided default value or a value from
        the default settings.

        Args:
            key (str): The key of the setting to retrieve.
            default (any, optional): An optional default value to return if the
                                     key is not found in the current settings and
                                     not present in the default settings.
                                     Defaults to None.

        Returns:
            any: The value of the setting, or the provided default value, or
                 the value from default settings if the key is not found.

        Example:
            >>> settings = SettingsManager()
            >>> settings.get("theme")
            'Light'
            >>> settings.get("non_existent_key", "Fallback Value")
            'Fallback Value'
            >>> settings.get("max_fps")
            30
        """
        return self.settings.get(
            key,
            default if default is not None else DEFAULT_SETTINGS.get(key)
        )

    def set(self, key, value):
        """
        Update a setting value and save it.

        :param key: The setting key to update
        :param value: The new value to store
        """
        self.settings[key] = value  # Update the setting in the current settings
        self.save()

    def all(self):
        """
        Returns all current settings as a dictionary.
        This allows accessing all settings at once, which is useful for saving
        or displaying a complete configuration view.

        Returns:
            dict: A dictionary containing all current settings.

        Example:
            >>> settings = SettingsManager()
            >>> all_settings = settings.all()
            >>> print(all_settings)
            {
                'theme': 'Light', 'language': 'English', 'ui_color_theme': 'Blue',
                'max_fps': 30, 'auto_update_saved_poses': False, 'joint_directions': {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
            }

        :return: dict of current settings
        """
        return self.settings