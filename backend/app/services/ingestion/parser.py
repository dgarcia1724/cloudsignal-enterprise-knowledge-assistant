"""Document parsing utilities."""

import json
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """
    Parse documents from various formats.

    Supported formats:
    - Markdown (.md)
    - JSON (.json)
    - YAML (.yaml, .yml)
    - Plain text (.txt)
    """

    SUPPORTED_FORMATS = {".md", ".json", ".yaml", ".yml", ".txt"}

    def parse(self, file_path: str | Path) -> str:
        """
        Parse document and return text content.

        Args:
            file_path: Path to document file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )

        logger.debug("parsing_document", file_path=str(file_path), format=suffix)

        if suffix == ".md":
            return self._parse_markdown(path)
        elif suffix == ".json":
            return self._parse_json(path)
        elif suffix in {".yaml", ".yml"}:
            return self._parse_yaml(path)
        else:
            return self._parse_text(path)

    def _parse_markdown(self, path: Path) -> str:
        """Parse markdown file."""
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # Remove YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content

    def _parse_json(self, path: Path) -> str:
        """Parse JSON file and convert to readable text."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Convert to formatted string
        return json.dumps(data, indent=2)

    def _parse_yaml(self, path: Path) -> str:
        """Parse YAML file and convert to readable text."""
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return yaml.dump(data, default_flow_style=False)

    def _parse_text(self, path: Path) -> str:
        """Parse plain text file."""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def get_document_title(self, content: str, file_path: str | Path) -> str:
        """
        Extract title from document content or filename.

        For markdown, uses first # heading.
        Falls back to filename.
        """
        path = Path(file_path)

        # Try to extract title from markdown heading
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()

        # Fall back to filename
        return path.stem.replace("-", " ").replace("_", " ").title()
