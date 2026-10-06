from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from d20.models import (
    Campaign,
    CampaignMembership,
    Character,
    GameSession,
    PreparationNote,
    SessionParticipation,
    User,
)


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (("Profile", {"fields": ("bio",)}),)
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            (
                "Profile",
                {"fields": ("first_name", "last_name", "email", "bio")},
            ),
        )
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "game_master", "status")
    list_filter = ("status",)
    search_fields = ("title",)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "character_class", "ancestry", "level", "owner")
    list_filter = ("character_class", "ancestry")
    search_fields = ("name",)


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "campaign", "scheduled_at", "status")
    list_filter = ("status", "campaign")
    search_fields = ("title",)


@admin.register(PreparationNote)
class PreparationNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "campaign", "author")
    list_filter = ("kind",)
    search_fields = ("title",)


admin.site.register(CampaignMembership)
admin.site.register(SessionParticipation)
