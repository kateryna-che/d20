from typing import Any, cast

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from d20.models import (
    Campaign,
    CampaignMembership,
    Character,
    GameSession,
    PreparationNote,
    SessionParticipation,
)


class RegistrationForm(UserCreationForm):
    """A new account: the name and the email next to the username and password."""

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = (*UserCreationForm.Meta.fields, "first_name", "last_name", "email")


class ProfileForm(forms.ModelForm):
    """The name, the email and the bio that a user keeps in the profile."""

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email", "bio")
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}
        help_texts = {
            "bio": "Favourite roles, experience, the time that suits you.",
        }


class CampaignForm(forms.ModelForm):
    """Create or update a campaign's details."""

    class Meta:
        model = Campaign
        fields = ("title", "description", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}


class MembershipForm(forms.ModelForm):
    """Let a player choose one of their own characters for the campaign."""

    class Meta:
        model = CampaignMembership
        fields = ("character",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Offer only characters owned by the campaign player."""
        super().__init__(*args, **kwargs)
        character_field = cast(forms.ModelChoiceField, self.fields["character"])
        character_field.queryset = Character.objects.filter(owner=self.instance.player)


class CharacterForm(forms.ModelForm):
    """Edit a character's stats, equipment and background."""

    class Meta:
        model = Character
        fields = (
            "name",
            "concept",
            "character_class",
            "ancestry",
            "level",
            *Character.ABILITIES,
            "max_hit_points",
            "hit_points",
            "armor_class",
            "speed",
            "abilities",
            "inventory",
            "notes",
            "backstory",
        )
        widgets = {
            "abilities": forms.Textarea(attrs={"rows": 6}),
            "inventory": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "backstory": forms.Textarea(attrs={"rows": 6}),
        }


class GameSessionForm(forms.ModelForm):
    """Plan a session or update its status and summary."""

    class Meta:
        model = GameSession
        fields = (
            "title",
            "scheduled_at",
            "play_location",
            "status",
            "agenda",
            "summary",
        )
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
            ),
            "agenda": forms.Textarea(attrs={"rows": 6}),
            "summary": forms.Textarea(attrs={"rows": 6}),
        }


class PreparationNoteForm(forms.ModelForm):
    """Add or edit a note shared with the campaign."""

    class Meta:
        model = PreparationNote
        fields = ("title", "kind", "content")


class ParticipationForm(forms.ModelForm):
    """The answer of a player to a game session: confirmed or declined."""

    class Meta:
        model = SessionParticipation
        fields = ("attendance_status",)


class SearchForm(forms.Form):
    """The search field of a list page."""

    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"type": "search", "aria-label": "Search"}),
    )

    def __init__(self, *args: Any, placeholder: str = "Search", **kwargs: Any) -> None:
        """Set the search placeholder for this list."""
        super().__init__(*args, **kwargs)
        self.fields["search"].widget.attrs["placeholder"] = placeholder
