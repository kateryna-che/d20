from django import forms

from d20.models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ("title", "description", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}