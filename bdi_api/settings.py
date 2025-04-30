import os
from pathlib import Path

class Settings:
    def __init__(self):
        self.source_url = "https://samples.adsbexchange.com/readsb-hist"
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = os.path.join(self.base_dir, "data")
        self.raw_dir = os.path.join(self.data_dir, "raw")
        self.prepared_dir = os.path.join(self.data_dir, "prepared")

        # Create necessary directories
        for directory in [self.data_dir, self.raw_dir, self.prepared_dir]:
            os.makedirs(directory, exist_ok=True)
