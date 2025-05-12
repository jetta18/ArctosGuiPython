"""
File: utils/settings_manager.py

This module provides the SettingsManager class for managing application settings in the Arctos GUI application.
Settings are persisted in a YAML file and loaded automatically on startup. Default settings are used if the configuration file is missing or corrupted.
"""

import os
import yaml

# Define the base directory and configuration file path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'user_config.yaml')

# Default settings used when the config file does not exist or is corrupted
DEFAULT_SETTINGS = {
    # The default application settings used if the configuration file is missing or corrupted.
    # Keys and values define UI theme, joint speeds, acceleration, directions, speed scaling,
    # live updates, homing offsets, and gear ratios.
    "theme": "Light",  # Default UI theme
    "joint_speeds": {i: 500 for i in range(6)},
    'joint_acceleration': {i: 150 for i in range(6)},
    "joint_directions": {i: 1 for i in range(6)},  # Default direction for each joint (1 or -1)
    "speed_scale": 1.0, 
    "enable_live_joint_updates": False,  # Enable live encoder updates in U
    "homing_offsets": {i: 0 for i in range(6)},  # Homing offset for each joint
    "gear_ratios": [13.5, 150, 150, 48, 33.91, 33.91],
    "coupled_axis_mode": False,  # Whether to use coupled B/C axis mode for axes 4 and 5
}

class SettingsManager:
    """
    Provides centralized loading, accessing, updating, and saving of application settings.
    Settings are stored in a YAML file and persist across different application sessions.
    If the configuration file is missing or corrupted, default settings are used.

    Attributes:
        settings (dict): The current application settings.
    """

    def __init__(self):
        """
        Initialize the SettingsManager instance.

        Loads settings from the YAML configuration file. If the configuration file does not exist,
        default settings are used and saved to a new file.

        Raises:
            Exception: If the configuration file exists but cannot be loaded due to corruption or permission errors.
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
        Save the current settings to the YAML configuration file.

        Raises:
            Exception: If writing to the configuration file fails due to I/O or permission errors.
        """
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(self.settings, f)

    def get(self, key, default=None):
        """
        Retrieve a setting value by key.

        If the key is not found in the current settings, returns the provided default value,
        or the value from DEFAULT_SETTINGS if the default is not specified.

        Args:
            key (str): The key of the setting to retrieve.
            default (Any, optional): The value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value of the setting, or the provided default, or the value from DEFAULT_SETTINGS.

        Example:
            >>> settings = SettingsManager()
            >>> settings.get("theme")
            'Light'
            >>> settings.get("non_existent_key", "Fallback Value")
            'Fallback Value'
        """
        return self.settings.get(
            key,
            default if default is not None else DEFAULT_SETTINGS.get(key)
        )

    def set(self, key, value):
        """
        Update a setting value and save it.

        Args:
            key (str): The setting key to update.
            value (Any): The new value to store.

        Returns:
            None
        """
        self.settings[key] = value  # Update the setting in the current settings
        self.save()

    def all(self):
        """
        Return all current settings as a dictionary.

        This allows accessing all settings at once, which is useful for saving
        or displaying a complete configuration view.

        Returns:
            dict: A dictionary containing all current settings.

        Example:
            >>> settings = SettingsManager()
            >>> all_settings = settings.all()
            >>> print(all_settings)
            {'theme': 'Light', 'joint_speeds': {0: 500, ...}, ...}
        """
        return self.settings