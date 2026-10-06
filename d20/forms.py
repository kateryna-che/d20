from django import forms

from d20.models import Campaign, GameSession


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ("title", "description", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}


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