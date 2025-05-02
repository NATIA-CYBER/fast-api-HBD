import os
from pathlib import Path

class Settings:
    def __init__(self):
        self.source_url = "https://samples.adsbexchange.com/readsb-hist"
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = os.path.join(self.base_dir, "data")
        self.raw_dir = os.path.join(self.data_dir, "raw", "day=20231101")
        self.prepared_dir = os.path.join(self.data_dir, "prepared")
        
        for directory in [self.data_dir, os.path.dirname(self.raw_dir), self.prepared_dir]:
            os.makedirs(directory, exist_ok=True)

# Create a single instance to be used throughout the application
settings = Settings()
