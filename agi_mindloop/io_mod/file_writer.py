from pathlib import Path

class FileWriter:
    """Safe file writer restricted to project directory."""

    def __init__(self, base_dir: str = "./data/output"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, filename: str, text: str) -> str:
        """Writes text to a file inside base_dir."""
        safe_name = filename.replace("/", "_")
        target = self.base_dir / safe_name
        with open(target, "w", encoding="utf-8") as f:
            f.write(text)
        return str(target)

