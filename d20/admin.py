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
    fieldsets = UserAdmin.fieldsets + ((("Profile", {"fields": ("bio",)}),))
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


@admin.register(CampaignMembership)
class CampaignMembershipAdmin(admin.ModelAdmin):
    list_display = ("player", "campaign", "character")


@admin.register(SessionParticipation)
class SessionParticipationAdmin(admin.ModelAdmin):
    list_display = ("membership", "game_session", "attendance_status")
    list_select_related = (
        "membership__player",
        "membership__campaign",
        "game_session",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "membership":
            kwargs["queryset"] = CampaignMembership.objects.select_related(
                "player", "campaign"
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
