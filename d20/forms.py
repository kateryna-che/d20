from django import forms
from django.contrib.auth import get_user_model

from d20.models import Campaign, GameSession, Character


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
