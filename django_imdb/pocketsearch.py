"""Pocketsearch related code."""

import logging

import pocketsearch  # type: ignore[import-untyped]
from django.conf import settings

from .models import Aka

logger = logging.getLogger(f"django_imdb.{__name__}")

# ignore these characters when indexing, they are not token seperators
IGNORE_CHARS = "'()."


class TitleSearchSchema(pocketsearch.Schema):  # type: ignore[misc]
    """Schema definition for pocketsearch."""

    # search_id is title_id+title combined,
    # it is used to identify unique entries in the index
    search_id = pocketsearch.Text(is_id_field=True)
    title_id = pocketsearch.Int(index=True)
    title = pocketsearch.Text(index=True)
    premiered_year = pocketsearch.Int(index=True)
    ended_year = pocketsearch.Int(index=True)
    rating = pocketsearch.Numeric(index=True)
    votes = pocketsearch.Int(index=True)


def title_search(title: str, year: int | None=None, database: str = "default") -> list[str]:
    """Do a pocketsearch search for a title."""
    with pocketsearch.PocketReader(
        db_name=settings.DATABASES[database]["NAME"],
        schema=TitleSearchSchema,
        index_name="pocketsearch_titles",
    ) as pocket_reader:
        if year is not None:
            results = pocket_reader.search(title=title, premiered_year=str(year)).order_by("rank", "-votes")
        else:
            results = pocket_reader.search(title=title).order_by("rank", "-votes")
    return [x.title_id for x in results]


def pocketsearch_normalise(string: str) -> str:
    """Normalise a string before adding to pocketsearch index."""
    string = pocketsearch.normalize(value=string)
    for char in IGNORE_CHARS:
        string = string.replace(char, "")
    return string


def reindex_pocketsearch(types: list[str], database: str = "default") -> None:
    """Reindex pocketsearch title search indexes."""
    akacount = Aka.objects.filter(title__title_type__in=types).count()
    indexed = 0
    batch_size = 100000
    while indexed < akacount:
        logger.info(f"Indexed {indexed} of {akacount} titles...")
        akas = [
            {
                "search_id": f"{aka.title.title_id}-{aka.aka}",
                "title_id": aka.title.title_id,
                "title": aka.aka,
                "premiered_year": aka.title.premiered,
                "ended_year": aka.title.ended,
                "rating": aka.title.rating.rating if hasattr(aka.title, "rating") else None,
                "votes": aka.title.rating.votes if hasattr(aka.title, "rating") else None,
            }
            for aka in Aka.objects.filter(title__title_type="movie").select_related("title__rating")[
                indexed : indexed + batch_size
            ]
        ]
        # insert batch into pocketsearch
        with pocketsearch.PocketWriter(
            db_name=settings.DATABASES[database]["NAME"],
            schema=TitleSearchSchema,
            index_name="pocketsearch_titles",
            normalize=pocketsearch_normalise,
        ) as pocket_writer:
            for akadict in akas:
                pocket_writer.insert_or_update(**akadict)
                indexed += 1
