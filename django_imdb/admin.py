"""Admin modules for django-imdb."""

from django.contrib import admin

from .models import Aka, AkaLanguage, AkaRegion, AkaType, Crew, CrewCategory, Episode, Person, Rating, Title, TitleType


@admin.register(TitleType)
class TitleTypeAdmin(admin.ModelAdmin[TitleType]):
    """Admin class for TitleType."""

    list_display = ["name"]


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin[Title]):
    """Admin class for Title."""

    list_display = [
        "title_id",
        "title_type",
        "primary_title",
        "original_title",
        "is_adult",
        "premiered",
        "ended",
        "runtime_minutes",
        "genres",
    ]
    list_filter = ["title_type", "is_adult"]
    search_fields = ["primary_title", "original_title", "premiered", "ended", "genres"]


###################################################################################################


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin[Person]):
    """Admin class for Person."""

    list_display = ["person_id", "name", "born", "died"]
    search_fields = ["name", "born", "died"]


###################################################################################################


@admin.register(AkaType)
class AkaTypeAdmin(admin.ModelAdmin[AkaType]):
    """Admin class for AkaType."""

    list_display = ["name"]


@admin.register(AkaRegion)
class AkaRegionAdmin(admin.ModelAdmin[AkaRegion]):
    """Admin class for AkaRegion."""

    list_display = ["name"]


@admin.register(AkaLanguage)
class AkaLanguageAdmin(admin.ModelAdmin[AkaLanguage]):
    """Admin class for AkaLanguage."""

    list_display = ["name"]


@admin.register(Aka)
class AkaAdmin(admin.ModelAdmin[Aka]):
    """Admin class for Aka."""

    list_display = ["title", "aka", "region", "language", "aka_type", "attributes", "is_original_title"]
    list_filter = ["region", "language"]


###################################################################################################


@admin.register(CrewCategory)
class CrewCategoryAdmin(admin.ModelAdmin[CrewCategory]):
    """Admin class for CrewCategory."""

    list_display = ["name"]


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin[Crew]):
    """Admin class for Crew."""

    list_display = ["id", "title", "person", "category", "job", "characters"]
    list_filter = ["category"]


###################################################################################################


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin[Episode]):
    """Admin class for Episode."""

    list_display = ["show_title", "episode_title", "season_number", "episode_number"]


###################################################################################################


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin[Rating]):
    """Admin class for Rating."""

    list_display = ["title_id", "rating", "votes"]
    list_filter = ["title_id"]
