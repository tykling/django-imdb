"""Export related functionality."""

from __future__ import annotations

import gzip
import logging
import time
from typing import TYPE_CHECKING, Any

from .models import Aka, Crew, Episode, Person, Rating, Title, TsvBaseModel

if TYPE_CHECKING:
    from pathlib import Path

    from django.db import models

logger = logging.getLogger(f"django_imdb.{__name__}")


def export_tsv_files(  # noqa: PLR0913
    *,
    export_dir: Path,
    skip_name_basics: bool = False,
    skip_title_basics: bool = False,
    skip_title_akas: bool = False,
    skip_title_principals: bool = False,
    skip_title_episodes: bool = False,
    skip_title_ratings: bool = False,
    **kwargs: dict[str, Any],
) -> None:
    """Export IMDB TSV files."""
    export_dir = export_dir.expanduser()
    export_dir.mkdir(parents=True, exist_ok=True)
    for tsvmodel in [Title, Person, Aka, Crew, Episode, Rating]:
        tsv = tsvmodel.TsvMeta
        if locals().get(tsv.skip_bool):
            logger.info(f"Skipping export of {tsv}")
            continue
        path = export_dir / tsv.filename
        objects = tsvmodel.objects.all()
        export_objects(
            export_dir=export_dir,
            model=tsvmodel,
            objects=objects,  # type: ignore[arg-type]
        )


def export_objects(
    export_dir: Path,
    model: type[TsvBaseModel],
    objects: models.QuerySet[Title | Person | Aka | Crew | Episode | Rating],
    batch_size: int = 100000,
) -> None:
    """Export IMDB data."""
    exported = 0
    tsv = model.TsvMeta
    totalstart = time.time()
    p = export_dir / tsv.filename
    logger.debug(f"Exporting file {p} ...")
    with gzip.open(p, "wt") as f:
        headers = "	".join([v[0] for k, v in tsv.fieldmap.items()])
        f.write(f"{headers}\n")
        # batching is only for reporting
        total = objects.count()
        logger.debug(f"Exporting {total} objects to TSV...")
        while exported < total:
            start = time.time()
            for obj in objects[exported : exported + batch_size]:
                if isinstance(obj, Title) and obj.primary_title == "PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER":
                    continue
                if isinstance(obj, Person) and obj.name == "PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER":
                    continue
                f.write(f"{obj.tsvline}\n")
                exported += 1
            duration = time.time() - start
            logger.debug(
                f"Exporting {exported}-{exported + batch_size} of {total} {model} django "
                f"objects took {round(duration, 2)} seconds, {round(batch_size / (duration))}/sec"
            )
    duration = time.time() - totalstart
    logger.info(
        f"Exported {exported} {model} objects in {round(duration, 2)} seconds, {round(exported / duration)}/sec"
    )
