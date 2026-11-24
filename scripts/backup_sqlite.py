import os
import shutil
from datetime import datetime
from pathlib import Path

source = Path(os.getenv("SQLITE_DATABASE_FILE", "dashboard_review.db"))
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

def backup():
    if not source.exists():
        raise FileNotFoundError(f"Database not found: {source}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = backup_dir / f"dashboard_review-{stamp}.db"
    shutil.copy2(source, destination)
    print(destination)

if __name__ == "__main__":
    backup()
