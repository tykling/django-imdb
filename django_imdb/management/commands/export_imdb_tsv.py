"""django-imdb management command to export IMDB TSV data."""

from __future__ import annotations

import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from django_imdb.export_tsv import export_tsv_files

logger = logging.getLogger(f"django_imdb.{__name__}")


class Command(BaseCommand):
    """Management command to export IMDB TSV data."""

    help = "Export TSV files"

    def add_arguments(self, parser: CommandParser) -> None:
        """Command-line arguments for the manage.py export_imdb_tsv command."""
        parser.add_argument("--export_dir", type=Path, default=Path("~/.cache/django-imdb-tsv-export"))
        parser.add_argument("--skip_name_basics", type=bool, default=False)
        parser.add_argument("--skip_title_basics", type=bool, default=False)
        parser.add_argument("--skip_title_akas", type=bool, default=False)
        parser.add_argument("--skip_title_principals", type=bool, default=False)
        parser.add_argument("--skip_title_episodes", type=bool, default=False)
        parser.add_argument("--skip_title_ratings", type=bool, default=False)

    def handle(self, *args: str, **options: dict[str, str | bool | Path]) -> None:  # noqa: ARG002
        """Export data to TSV files."""
        self.stdout.write(self.style.SUCCESS("Beginning export"))
        logging.basicConfig(level=logging.DEBUG)
        logger.debug(options)
        export_tsv_files(**options)  # type: ignore[arg-type]
        self.stdout.write(self.style.SUCCESS(f"Export done! Files can be found in {options['export_dir']}"))
