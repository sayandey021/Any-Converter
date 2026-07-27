import os
import json
import datetime
from src.backend.settings import SettingsManager

class HistoryManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HistoryManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.settings = SettingsManager()
        from src.backend.settings import SETTINGS_FILE
        self.history_file = os.path.join(os.path.dirname(SETTINGS_FILE), "history.json")
        self.records = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_record(self, input_path, target_format, status, output_path=None, error_message=None):
        record = {
            "input_path": input_path,
            "filename": os.path.basename(input_path),
            "target_format": target_format,
            "status": status,
            "output_path": output_path,
            "error_message": error_message,
            "timestamp": datetime.datetime.now().isoformat()
        }
        # Add to beginning of the list
        self.records.insert(0, record)
        # Keep only the last 100 records to prevent file from growing indefinitely
        self.records = self.records[:100]
        self._save_history()

    def get_history(self):
        return self.records
        
    def clear_history(self):
        self.records = []
        self._save_history()

    def remove_record(self, record):
        if record in self.records:
            self.records.remove(record)
            self._save_history()
