from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import generic

from d20.forms import CharacterForm
from d20.models import Character
from d20.views.mixins import OwnerRequiredMixin, ReturnUrlMixin, SearchMixin


class CharacterListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    """The characters of the logged-in user.

    Characters of other players are opened from campaign pages.
    """

    model = Character
    ordering = ("name", "pk")
    paginate_by = 8
    search_field = "name"
    search_placeholder = "Character name…"

    def get_queryset(self) -> QuerySet[Character]:
        return super().get_queryset().filter(owner=self.request.user)


class CharacterDetailView(LoginRequiredMixin, generic.DetailView):
    """The sheet of a character: any logged-in user may read it.

    The page lists the campaigns of the character and the answers of its
    player to their sessions.
    """

    queryset = Character.objects.select_related("owner").prefetch_related(
        "memberships__campaign",
        "memberships__participations__game_session",
    )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Gather the answers from all memberships of the character in one list."""
        context = super().get_context_data(**kwargs)
        context["participations"] = [
            participation
            for membership in self.object.memberships.all()
            for participation in membership.participations.all()
        ]
        return context


class CharacterCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    """A logged-in user creates a character and becomes its owner."""

    model = Character
    form_class = CharacterForm
    success_url = reverse_lazy("d20:character-list")
    success_message = "The character was created."

    def form_valid(self, form: ModelForm) -> HttpResponse:
        """Make the user the owner of the new character."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CharacterUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    """The owner edits the character sheet."""

    model = Character
    form_class = CharacterForm
    owner_field = "owner"
    success_message = "The character sheet was saved."


class CharacterDeleteView(OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """The owner deletes the character.

    The owner stays in the campaigns of the character, but without one.
    """

    model = Character
    owner_field = "owner"
    success_url = reverse_lazy("d20:character-list")
    success_message = "The character was deleted."
