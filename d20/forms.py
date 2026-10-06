from django import forms
from django.contrib.auth import get_user_model

from d20.models import (
    Campaign,
    GameSession,
    Character,
    CampaignMembership,
    PreparationNote,
    SessionParticipation,
)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email", "bio")
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}
        help_texts = {
            "bio": "Favourite roles, experience, the time that suits you.",
        }


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ("title", "description", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}


class MembershipForm(forms.ModelForm):
    """A player chooses one of the own characters for the campaign."""

    class Meta:
        model = CampaignMembership
        fields = ("character",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["character"].queryset = Character.objects.filter(
            owner=self.instance.player
        )


class CharacterForm(forms.ModelForm):
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
    class Meta:
        model = PreparationNote
        fields = ("title", "kind", "content")


class ParticipationForm(forms.ModelForm):
    class Meta:
        model = SessionParticipation
        fields = ("attendance_status",)


class SearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search", "type": "search"}),
    )
