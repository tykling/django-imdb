"""django-imdb management command to download and import IMDB TSV data."""

from __future__ import annotations

import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from django_imdb.import_tsv import import_tsv_files

logger = logging.getLogger(f"django_imdb.{__name__}")


class Command(BaseCommand):
    """Management command to import IMDB TSV data."""

    help = "Import TSV files"

    def add_arguments(self, parser: CommandParser) -> None:
        """Command-line arguments for the manage.py import_imdb_tsv command."""
        parser.add_argument("--download_dir", type=Path, default=Path("~/.cache/django-imdb-tsv-data"))
        parser.add_argument("--download_host", type=str, default="datasets.imdbws.com")
        parser.add_argument("--skip_name_basics", type=bool, default=False)
        parser.add_argument("--skip_title_basics", type=bool, default=False)
        parser.add_argument("--skip_title_akas", type=bool, default=False)
        parser.add_argument("--skip_title_principals", type=bool, default=False)
        parser.add_argument("--skip_title_episodes", type=bool, default=False)
        parser.add_argument("--skip_title_ratings", type=bool, default=False)
        parser.add_argument("--max_tsv_age_seconds", type=int, default=86400)

    def handle(self, *args: str, **options: dict[str, str | bool | Path]) -> None:  # noqa: ARG002
        """Do the thing."""
        self.stdout.write(self.style.SUCCESS("Beginning import"))
        logging.basicConfig(level=logging.DEBUG)
        logger.debug(options)
        import_tsv_files(**options)  # type: ignore[arg-type]
