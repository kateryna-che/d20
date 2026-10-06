from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.views import generic

from d20.forms import PreparationNoteForm
from d20.models import Campaign, PreparationNote
from d20.views.mixins import (
    CampaignRelatedCreateMixin,
    OwnerRequiredMixin,
    ReturnUrlMixin,
)


class PreparationNoteDetailView(LoginRequiredMixin, generic.DetailView):
    """A note is open to the game master and the players of its campaign."""

    queryset = PreparationNote.objects.select_related("campaign", "author")

    def get_queryset(self):
        campaigns = Campaign.objects.for_user(self.request.user)
        return super().get_queryset().filter(campaign__in=campaigns)


class PreparationNoteCreateView(
    LoginRequiredMixin,
    CampaignRelatedCreateMixin,
    SuccessMessageMixin,
    generic.CreateView,
):
    """The game master or a player adds a note to the campaign from the URL."""

    model = PreparationNote
    form_class = PreparationNoteForm
    success_message = "The note was added."

    def get_campaigns(self):
        return Campaign.objects.for_user(self.request.user)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PreparationNoteUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    """The author edits the note while in its campaign."""

    model = PreparationNote
    form_class = PreparationNoteForm
    owner_field = "author"
    success_message = "The note was saved."

    def get_queryset(self):
        campaigns = Campaign.objects.for_user(self.request.user)
        return super().get_queryset().filter(campaign__in=campaigns)


class PreparationNoteDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
    """The author in the campaign or its game master deletes the note."""

    model = PreparationNote
    success_message = "The note was deleted."

    def get_queryset(self):
        user = self.request.user
        return (
            super()
            .get_queryset()
            .filter(
                Q(author=user) | Q(campaign__game_master=user),
                campaign__in=Campaign.objects.for_user(user),
            )
        )

    def get_success_url(self):
        return self.object.campaign.get_absolute_url()
