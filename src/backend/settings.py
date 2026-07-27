import json
import os
import tempfile

import sys

if getattr(sys, 'frozen', False):
    # If packaged, store settings in a persistent user directory
    _app_data_dir = os.path.join(os.path.expanduser('~'), '.AnyConverter')
    os.makedirs(_app_data_dir, exist_ok=True)
    SETTINGS_FILE = os.path.join(_app_data_dir, 'settings.json')
else:
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'settings.json')
DEFAULTS = {
    'output_dir': '',  # Empty means same as input file directory
    'temp_dir': os.path.join(tempfile.gettempdir(), 'Any Converter'),
    
    # General / Performance
    'max_concurrent_jobs': 3,
    
    # Video Settings
    'hw_accel': 'auto',          # 'auto', 'none', 'nvenc', 'qsv', 'amf'
    'default_video_codec': 'h264', # 'h264', 'hevc', 'copy'
    'video_preset': 'medium',      # 'fast', 'medium', 'slow'
    
    # Audio Settings
    'default_audio_codec': 'aac',  # 'aac', 'mp3', 'copy'
    'audio_bitrate': '192k',       # '128k', '192k', '320k'
    
    # Appearance
    'theme': 'dark',  # 'dark' or 'light'
    'accent_color': 'Violet',
    'bg_image_path': '',
    'bg_image_opacity': 0.1,
}


class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = {}
            cls._instance._load()
        return cls._instance

    def _load(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
        except Exception:
            self._settings = {}
        # Fill in any missing keys with defaults
        for key, value in DEFAULTS.items():
            if key not in self._settings:
                self._settings[key] = value
                
        # Enforce temp_dir is not empty
        if not self._settings.get('temp_dir'):
            self._settings['temp_dir'] = DEFAULTS['temp_dir']

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default if default is not None else DEFAULTS.get(key))

    def set(self, key, value):
        self._settings[key] = value

    def all(self):
        return dict(self._settings)

    def reset(self):
        self._settings = dict(DEFAULTS)
        self.save()

