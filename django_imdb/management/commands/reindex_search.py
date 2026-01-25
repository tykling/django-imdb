"""django-imdb management command to reindex search indexes."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from django_imdb.pocketsearch import reindex_pocketsearch
from django_imdb.utils import get_loglevel


class Command(BaseCommand):
    """Management command to reindex title search."""

    help = "Reindex title search"

    def handle(self, *args: str, **options: dict[str, str | int]) -> None:  # noqa: ARG002
        """Reindex title search data."""
        self.stdout.write(self.style.SUCCESS("Beginning reindex"))
        logging.basicConfig(level=get_loglevel(verbosity=options["verbosity"]))  # type: ignore[arg-type]
        # Index movies only for now.
        reindex_pocketsearch(types=["movie"])
        self.stdout.write(self.style.SUCCESS("Reindex done!"))
