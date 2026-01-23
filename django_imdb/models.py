"""Model definitions for django-imdb."""

import os
from pathlib import Path
from typing import ClassVar

from django.db import models


class TsvBaseModel(models.Model):
    """Abstract model for TSV based model."""

    class Meta:
        """Abstract model."""

        abstract = True

    class TsvMeta:
        """Data structure for the IMDB TSV file this model is based on."""

        filename: Path
        fieldmap: ClassVar[dict[str, tuple[str, type, type]]] = {}
        get_or_create_fks: ClassVar[dict[str, tuple[type[models.Model], str]]]
        unique_fields: ClassVar[list[str]]
        skip_bool: str
        type_casts: ClassVar[dict[str, tuple[type, type]]] = {}

    @property
    def tsvline(self) -> str:
        """Return a string representation of this model instance suitable for export to an IMDB TSV file."""
        elements = []
        for key in type(self).TsvMeta.fieldmap:
            # get value
            value = getattr(self, key)
            if value is not None:
                # cast to correct type
                elements.append(self.TsvMeta.fieldmap[key][2](value))
            else:
                # use imdb nulls
                elements.append("\\N")
        return "\t".join([str(x) for x in elements])


class TitleType(models.Model):
    """The type of a title like movie or tvEpisode."""

    name: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The type.")

    def __str__(self) -> str:
        """Return a string representation of this TitleType."""
        return self.name


class Title(TsvBaseModel):
    """Titles. The basic IMDB unit which everything else relates to."""

    title_id: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The main title ID.")
    title_type: models.ForeignKey[TitleType, TitleType] = models.ForeignKey(
        "TitleType",
        default="PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER",
        on_delete=models.PROTECT,
        related_name="titles",
    )
    primary_title: models.CharField[str, str] = models.CharField(
        default="PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER",
        help_text="The primary/most used title of the movie",
    )
    original_title: models.CharField[str, str] = models.CharField(
        default="PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER",
        help_text="The original title of the movie, in the original language.",
    )
    is_adult: models.BooleanField[bool, bool] = models.BooleanField(default=False)
    premiered: models.IntegerField[int, int] = models.IntegerField(
        blank=True, null=True, help_text="The year of the premiere of this title."
    )
    ended: models.IntegerField[int, int] = models.IntegerField(
        blank=True, null=True, help_text="End year (for TV series only)."
    )
    runtime_minutes: models.IntegerField[int, int] = models.IntegerField(
        blank=True, null=True, help_text="The runtime in minutes of this title."
    )
    genres: models.CharField[str, str] = models.CharField(blank=True, help_text="Up to three genres for this title.")

    class Meta:
        """Set ordering."""

        ordering = ["title_id"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("title.basics.tsv.gz")
        fieldmap = {
            "title_id": ("tconst", str, str),
            "title_type_id": ("titleType", str, str),
            "primary_title": ("primaryTitle", str, str),
            "original_title": ("originalTitle", str, str),
            "is_adult": ("isAdult", bool, int),
            "premiered": ("startYear", int, int),
            "ended": ("endYear", int, int),
            "runtime_minutes": ("runtimeMinutes", int, int),
            "genres": ("genres", str, str),
        }
        get_or_create_fks = {"title_type_id": (TitleType, "name")}
        unique_fields = ["title_id"]
        skip_bool = "skip_title_basics"

    def __str__(self) -> str:
        """Return a string representation of this Title."""
        return f"{self.title_id} ({self.title_type}) - {self.primary_title} ({self.premiered})"

    @property
    def imdb_url(self) -> str:
        """Return IMDB url for this title."""
        return f"https://www.imdb.com/title/{self.title_id}/"

    @property
    def genrelist(self) -> list[str]:
        """Return a list of genres."""
        return self.genres.split(",")

    @property
    def yearlist(self) -> list[str]:
        """Return a list of years."""
        if self.premiered and self.ended:
            # this title has an end year
            return [str(x) for x in range(self.premiered, self.ended + 1)]
        if self.premiered:
            # this title only has a premiered year
            return [str(self.premiered)]
        # no years available
        return []

    @property
    def dirname(self) -> str:
        """Return a suitable dirname for this title."""
        return f"{self.primary_title} ({self.premiered})".replace(os.sep, "_")


###################################################################################################


class Person(TsvBaseModel):
    """Human beings. In the IMDB data not everyone has a name, and far from everyone has born/died years."""

    person_id: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The main person ID")
    name: models.CharField[str, str] = models.CharField(
        blank=True,
        default="PLAYTIME_IMDB_DATA_INCONSISTENCY_PLACEHOLDER",
        help_text="The name of this person (when known)",
    )
    born: models.IntegerField[int, int] = models.IntegerField(
        blank=True, null=True, help_text="Birth year of this person (when known)"
    )
    died: models.IntegerField[int, int] = models.IntegerField(
        blank=True, null=True, help_text="Death year of this person (when known)"
    )
    primary_professions: models.CharField[str, str] = models.CharField(
        blank=True,
        help_text="Comma-separated list of up to three primary professions for this person.",
    )
    known_for_titles: models.CharField[str, str] = models.CharField(
        blank=True,
        help_text="The titles this person is most known for working on.",
    )

    class Meta:
        """Set ordering."""

        ordering = ["person_id"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("name.basics.tsv.gz")
        fieldmap = {
            "person_id": ("nconst", str, str),
            "name": ("primaryName", str, str),
            "born": ("birthYear", int, int),
            "died": ("deathYear", int, int),
            "primary_professions": ("primaryProfession", str, str),
            "known_for_titles": ("knownForTitles", str, str),
        }
        get_or_create_fks = {}
        unique_fields = ["person_id"]
        skip_bool = "skip_name_basics"

    def __str__(self) -> str:
        """Return a string representation of a person."""
        return (
            f"{self.person_id} {self.name} ({self.born if self.born else 'unknown'}-"
            f"{self.died if self.died else 'unknown'})"
        )


###################################################################################################


class AkaType(models.Model):
    """Types of AKAs (alternative titles)."""

    name: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The type name.")

    def __str__(self) -> str:
        """Return a string representation of AkaType."""
        return self.name


class AkaRegion(models.Model):
    """Regions for AKAs (alternative titles)."""

    name: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The region name.")

    def __str__(self) -> str:
        """Return a string representation of AkaRegion."""
        return self.name


class AkaLanguage(models.Model):
    """Languages for AKAs (alternative titles)."""

    name: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The language name.")

    def __str__(self) -> str:
        """Return a string representation of AkaLanguage."""
        return self.name


class Aka(TsvBaseModel):
    """Original and alternative titles. title.akas.tsv.gz."""

    title: models.ForeignKey[Title, Title] = models.ForeignKey("Title", on_delete=models.PROTECT, related_name="akas")
    ordering: models.IntegerField[int, int] = models.IntegerField()
    aka: models.CharField[str, str] = models.CharField(help_text="The title/AKA.")
    region: models.ForeignKey[AkaRegion, AkaRegion] = models.ForeignKey(
        "AkaRegion",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="akas",
        help_text="The region of this AKA (where relevant)",
    )
    language: models.ForeignKey[AkaLanguage, AkaLanguage] = models.ForeignKey(
        "AkaLanguage",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="akas",
        help_text="The language of this AKA (where relevant)",
    )
    aka_type: models.ForeignKey[AkaType, AkaType] = models.ForeignKey(
        "AkaType",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="akas",
        help_text="The type of this AKA",
    )
    attributes: models.CharField[str, str] = models.CharField(
        blank=True, help_text="Additional comma-separated attributes for this title."
    )
    is_original_title: models.BooleanField[bool, bool] = models.BooleanField()

    class Meta:
        """Set ordering."""

        ordering = ["title", "ordering"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("title.akas.tsv.gz")
        fieldmap = {
            "title_id": ("titleId", str, str),
            "ordering": ("ordering", int, int),
            "aka": ("title", str, str),
            "region_id": ("region", str, str),
            "language_id": ("language", str, str),
            "aka_type_id": ("types", str, str),
            "attributes": ("attributes", str, str),
            "is_original_title": ("isOriginalTitle", bool, int),
        }
        get_or_create_fks = {
            "title_id": (Title, "title_id"),
            "region_id": (AkaRegion, "name"),
            "language_id": (AkaLanguage, "name"),
            "aka_type_id": (AkaType, "name"),
        }
        unique_fields = ["id"]
        skip_bool = "skip_title_akas"

    def __str__(self) -> str:
        """Return a string representation of an Aka."""
        return (
            f"{self.title.title_type} {self.title.title_id} '{self.title.primary_title}' AKA "
            f"'{self.aka}' (type: {self.aka_type or 'N/A'}, language: {self.language or 'N/A'}, "
            f"region: {self.region or 'N/A'})"
        )


###################################################################################################


class CrewCategory(models.Model):
    """The category of work done by a person on a title (movie/episode)."""

    name: models.CharField[str, str] = models.CharField(primary_key=True, help_text="The category")

    def __str__(self) -> str:
        """Return a string representation of a CrewCategory."""
        return self.name


class Crew(TsvBaseModel):
    """Crew members. title.principals.tsv.gz. Some categories of work has more than one job."""

    title: models.ForeignKey[Title, Title] = models.ForeignKey(
        "Title", on_delete=models.PROTECT, related_name="crewmembers"
    )
    ordering: models.IntegerField[int, int] = models.IntegerField()
    person: models.ForeignKey[Person, Person] = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="crews"
    )
    category: models.ForeignKey[CrewCategory, CrewCategory] = models.ForeignKey(
        "CrewCategory", on_delete=models.PROTECT, related_name="crews"
    )
    job: models.CharField[str, str] = models.CharField(
        blank=True, help_text="The job performed by this crewmember (where relevant)"
    )
    characters: models.CharField[str, str] = models.CharField(
        blank=True, help_text="The characters played by this crewmember (where relevant)"
    )

    class Meta:
        """Set ordering."""

        ordering = ["title", "ordering"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("title.principals.tsv.gz")
        fieldmap = {
            "title_id": ("tconst", str, str),
            "ordering": ("ordering", int, int),
            "person_id": ("nconst", str, str),
            "category_id": ("category", str, str),
            "job": ("job", str, str),
            "characters": ("characters", str, str),
        }
        get_or_create_fks = {
            "title_id": (Title, "title_id"),
            "person_id": (Person, "person_id"),
            "category_id": (CrewCategory, "name"),
        }
        unique_fields = ["id"]
        skip_bool = "skip_title_principals"

    def __str__(self) -> str:
        """Return a string representation."""
        played = f"(played {self.clean_characters}) " if self.characters else ""
        return f"{self.person} worked as {self.category} {played}on {self.title}"

    @property
    def clean_characters(self) -> str:
        """Return a version of characters without []."""
        return str(self.characters.replace("[", "").replace("]", ""))


###################################################################################################


class Episode(TsvBaseModel):
    """Episodes of TV shows. Not all shows have seasons and/or episode numbers."""

    show_title: models.ForeignKey[Title, Title] = models.ForeignKey(
        "Title", on_delete=models.PROTECT, related_name="tvshows"
    )
    episode_title: models.ForeignKey[Title, Title] = models.ForeignKey(
        "Title", on_delete=models.PROTECT, related_name="episodes"
    )
    season_number: models.IntegerField[int, int] = models.IntegerField(blank=True, null=True)
    episode_number: models.IntegerField[int, int] = models.IntegerField(blank=True, null=True)

    class Meta:
        """Set ordering."""

        ordering = ["show_title"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("title.episode.tsv.gz")
        fieldmap = {
            "show_title_id": ("parentTconst", str, str),
            "episode_title_id": ("tconst", str, str),
            "season_number": ("seasonNumber", int, int),
            "episode_number": ("episodeNumber", int, int),
        }
        get_or_create_fks = {
            "show_title_id": (Title, "title_id"),
            "episode_title_id": (Title, "title_id"),
        }
        unique_fields = ["id"]
        skip_bool = "skip_title_episodes"

    def __str__(self) -> str:
        """Return a string representation of an Episode."""
        return f"Show {self.show_title} episode {self.episode_title}"


###################################################################################################


class Rating(TsvBaseModel):
    """Ratings."""

    title: models.OneToOneField[Title, Title] = models.OneToOneField("Title", on_delete=models.PROTECT)
    rating: models.FloatField[float, float] = models.FloatField()
    votes: models.IntegerField[int, int] = models.IntegerField()

    class Meta:
        """Set ordering."""

        ordering = ["title"]

    class TsvMeta(TsvBaseModel.TsvMeta):
        """Data structure for the TSV file this model is based on."""

        filename = Path("title.ratings.tsv.gz")
        fieldmap = {
            "title_id": ("tconst", str, str),
            "rating": ("averageRating", float, float),
            "votes": ("numVotes", int, int),
        }
        get_or_create_fks = {
            "title_id": (Title, "title_id"),
        }
        unique_fields = ["title"]
        skip_bool = "skip_title_ratings"

    def __str__(self) -> str:
        """Return a string representation of a Rating."""
        return f"{self.title} rating {self.rating} ({self.votes} votes)"
