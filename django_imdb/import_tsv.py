"""Import related functionality."""

from __future__ import annotations

import gzip
import logging
import random
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

from .models import Aka, Crew, Episode, Person, Rating, Title, TitleType, TsvBaseModel
from .pocketsearch import reindex_pocketsearch
from .utils import count_lines, download_file

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

MiB = 1024 * 1024
logger = logging.getLogger(f"django_imdb.{__name__}")


def import_tsv_files(  # noqa: PLR0913
    *,
    download_dir: Path = Path("~/.cache/django-imdb-tsv-data"),
    download_host: str = "datasets.imdbws.com",
    skip_name_basics: bool = False,
    skip_title_basics: bool = False,
    skip_title_akas: bool = False,
    skip_title_principals: bool = False,
    skip_title_episodes: bool = False,
    skip_title_ratings: bool = False,
    max_tsv_age_seconds: int = 86400 * 14,
    **kwargs: dict[str, int | None | bool],
) -> None:
    """Download IMDB TSV files (if needed) and call import_objects() for each TSV file."""
    # create placeholder TitleType
    TitleType.objects.get_or_create(name="PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER")
    download_dir.expanduser().mkdir(parents=True, exist_ok=True)
    for tsvmodel in [Title, Person, Aka, Crew, Episode, Rating]:
        tsv = tsvmodel.TsvMeta
        if locals().get(tsv.skip_bool):
            logger.info(f"Skipping import of {tsv}")
            continue
        path = download_dir / tsv.filename
        if path.exists() and time.time() - path.stat().st_mtime > max_tsv_age_seconds:
            logger.debug(f"TSV file {path} is older than {max_tsv_age_seconds}, delete+re-download...")
            path.unlink()
        if not path.exists():
            url = f"https://{download_host}/{tsv.filename}"
            logger.info(f"Downloading file {url} ...")
            download_file(url=url, path=path)
        import_objects(basedir=download_dir, model=tsvmodel)
    # done, update search index before exiting. Index movies only for now.
    reindex_pocketsearch(types=["movie"])


def import_objects(
    basedir: Path,
    model: type[TsvBaseModel],
    batch_size: int = 100000,
) -> None:
    """Read a TSV file and create Django objects for each row."""
    objects: list[TsvBaseModel] = []
    imported = 0
    tsv = model.TsvMeta
    known_fks: dict[str, set[str]] = {fk: set() for fk in tsv.get_or_create_fks}
    totalstart = time.time()
    p = basedir / tsv.filename
    with gzip.open(p, "rt") as f:
        lines = count_lines(f=f)
    logger.info(f"Importing file {p} (file contains {lines} records)...")
    with gzip.open(p, "rt") as f:
        for importcount, row in enumerate(tsvreader(f)):
            if not objects:
                # starting new batch
                logger.debug(f"Creating batch of up to {batch_size} in-memory {model} django objects...")
                start = time.time()
            # make sure needed FKs are created before they are needed
            for fk, (fkmodel, field) in tsv.get_or_create_fks.items():
                rowkey = tsv.fieldmap[fk][0]
                if row[rowkey] and row[rowkey] not in known_fks[fk]:
                    # make sure this FK exists in the database
                    kwargs: dict[str, Any | None] = {field: row[rowkey]}
                    obj, created = fkmodel.objects.get_or_create(**kwargs)
                    if created:
                        logger.debug(f"New value '{row[rowkey]}' for fk {fk} found - created in {fkmodel} in database")
                    known_fks[fk].add(getattr(obj, field))
            # build object kwargs
            kwargs = {}
            for field, (column, import_cast, export_cast) in tsv.fieldmap.items():
                value = row[column]
                if value is None:
                    # this field was \N in the TSV,
                    # use "" for strings, use None for other types (including FKs)
                    kwargs[field] = "" if import_cast is str and field not in tsv.get_or_create_fks else None
                else:
                    kwargs[field] = import_cast(export_cast(value))
            # create object in memory
            obj = model(**kwargs)
            objects.append(obj)
            if len(objects) == batch_size:
                # create batch of objects in DB
                create_objects(objects=objects)
                imported += len(objects)
                duration = time.time() - start
                percent = round((imported / lines) * 100, 2)
                logger.info(
                    f"Imported {percent}% ({importcount} out of {lines} total records). "
                    f"Creating latest batch of {len(objects)} {model} in DB took "
                    f"{round(duration, 2)} seconds, {round(len(objects) / (duration))}/sec"
                )
                objects = []
        if objects:
            # create the last batch
            create_objects(objects=objects)
            imported += len(objects)
    duration = time.time() - totalstart
    logger.info(
        f"Done! Imported or updated {imported} {model} objects in "
        f"{round(duration, 2)} seconds, {round(imported / duration)}/sec"
    )


def tsvreader(f: TextIO) -> Generator[dict[str, str | None]]:
    r"""Yield dicts of lines from IMDB TSV. Interpret \N as None. Inspired by imdb-sqlite."""
    keys = [x.strip() for x in next(f).split("\t")]
    for row in f:
        values = [(x.strip() if x and x != "\\N" else None) for x in row.rstrip().split("\t")]
        yield dict(zip(keys, values, strict=False))


def create_objects(
    objects: Sequence[TsvBaseModel],
    bulk_create_batch_size: int = 1000,
) -> None:
    """Create a bunch of objects using bulk_create."""
    model = type(objects[0])
    tsv = model.TsvMeta
    logger.debug(f"Creating or updating {len(objects)} {model} objects in database")
    start = time.time()
    result = model.objects.bulk_create(
        objs=objects,
        update_conflicts=True,
        update_fields=list(set(tsv.fieldmap.keys()).difference(tsv.unique_fields)),
        unique_fields=tsv.unique_fields,
        batch_size=bulk_create_batch_size,
    )
    duration = time.time() - start
    logger.debug(
        f"Creating {len(objects)} {len(result)} {model} objects in database took "
        f"{round(duration, 2)} seconds, {round(len(objects) / (duration))}/sec"
    )
    rand = random.randint(0, len(objects) - 1)  # noqa: S311
    logger.info(f"Random sample: {objects[rand]}")
