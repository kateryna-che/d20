from collections import Counter
from operator import attrgetter
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Exists, OuterRef, Prefetch, QuerySet
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from d20.forms import CampaignForm, MembershipForm
from d20.models import Campaign, CampaignMembership, GameSession, PreparationNote
from d20.views.mixins import (
    AuthenticatedHttpRequest,
    OwnerRequiredMixin,
    ReturnUrlMixin,
    SearchMixin,
)


class CampaignListView(SearchMixin, generic.ListView):
    """The campaigns of all game masters: guests may look through them too.

    A card shows the party of the campaign and its next session.
    """

    queryset = (
        Campaign.objects.select_related("game_master")
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=CampaignMembership.objects.select_related("character"),
            )
        )
        .annotate(sessions_count=Count("game_sessions"))
        .order_by("-created_at")
    )
    paginate_by = 6
    search_placeholder = "Campaign title…"

    def get_queryset(self) -> QuerySet[Campaign]:
        """Add the upcoming sessions to every campaign of the list.

        For a logged-in user a campaign also says in "is_player" whether
        the user plays in it.
        """
        upcoming_sessions = GameSession.objects.filter(
            status=GameSession.Status.SCHEDULED, scheduled_at__gte=timezone.now()
        ).order_by("scheduled_at")
        campaigns: QuerySet[Campaign] = (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "game_sessions",
                    queryset=upcoming_sessions,
                    to_attr="upcoming_sessions",
                )
            )
        )
        user = self.request.user
        if not user.is_authenticated:
            return campaigns
        own_memberships = CampaignMembership.objects.filter(
            campaign=OuterRef("pk"), player=user
        )
        return campaigns.annotate(is_player=Exists(own_memberships))


class CampaignDetailView(generic.DetailView):
    """The page of a campaign: guests may read it too.

    The template keeps the names of the players and the places of the
    sessions from a guest.
    """

    queryset = Campaign.objects.select_related("game_master").prefetch_related(
        "memberships__player", "memberships__character", "game_sessions"
    )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Tell the template who the visitor is in the campaign.

        The notes are added only for the game master and the players.
        """
        context = super().get_context_data(**kwargs)
        context["is_game_master"] = self.object.game_master_id == self.request.user.pk
        context["is_player"] = any(
            membership.player_id == self.request.user.pk
            for membership in self.object.memberships.all()
        )
        context["can_join"] = (
            not context["is_game_master"]
            and not context["is_player"]
            and self.object.status != Campaign.Status.COMPLETED
        )
        if context["is_game_master"] or context["is_player"]:
            context.update(self.get_notes_context())
        context["session_groups"] = self.get_session_groups()
        return context

    def get_notes_context(self) -> dict[str, Any]:
        """Notes of the campaign and the filter by their kinds.

        The kind comes from "kind" of the query string. The filter offers
        only the kinds that the campaign has notes of; any other value
        shows every note.
        """
        notes = list(self.object.notes.select_related("author"))
        kind_counts = Counter(note.kind for note in notes)
        active_kind = self.request.GET.get("kind", "")
        if active_kind not in kind_counts:
            active_kind = ""
        return {
            "notes": [
                note for note in notes if not active_kind or note.kind == active_kind
            ],
            "notes_count": len(notes),
            "note_kinds": [
                (kind.value, kind.label, kind_counts[kind.value])
                for kind in PreparationNote.Kind
                if kind_counts[kind.value]
            ],
            "active_kind": active_kind,
        }

    def get_session_groups(self) -> list[tuple[str, list[GameSession]]]:
        """Sessions of the campaign under their statuses, scheduled ones first.

        The nearest scheduled session comes first, played ones start from
        the latest.
        """
        campaign_sessions = self.object.game_sessions.all()
        groups = []
        for status in GameSession.Status:
            game_sessions = [
                game_session
                for game_session in campaign_sessions
                if game_session.status == status
            ]
            if status == GameSession.Status.SCHEDULED:
                game_sessions.sort(key=attrgetter("scheduled_at"))
            if game_sessions:
                groups.append((status.label, game_sessions))
        return groups


class CampaignCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    """A logged-in user starts a campaign and becomes its game master."""

    model = Campaign
    form_class = CampaignForm
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was created. You are its game master."

    def form_valid(self, form: ModelForm) -> HttpResponse:
        """Make the user the game master of the new campaign."""
        form.instance.game_master = self.request.user
        return super().form_valid(form)


class CampaignUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    """The game master edits the campaign."""

    model = Campaign
    form_class = CampaignForm
    success_message = "The campaign was updated."


class CampaignDeleteView(OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """The game master deletes the campaign with its sessions and notes."""

    model = Campaign
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was deleted."


class CampaignMembershipView(LoginRequiredMixin, generic.View):
    """Join or leave the campaign according to the submitted action.

    The game master runs the campaign and is not on its player list.
    A completed campaign takes no new players; those in it may leave.
    """

    def get(self, request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
        """Lead to the campaign page: only its form changes the membership."""
        return redirect("d20:campaign-detail", pk=pk)

    def post(self, request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
        """Join or leave; a repeated action changes nothing.

        An unknown action gets 400, a campaign closed to the action gets 404.
        """
        action = request.POST.get("action")
        if action not in ("join", "leave"):
            return HttpResponseBadRequest("Invalid membership action.")

        campaigns = Campaign.objects.exclude(game_master=request.user)
        if action == "join":
            campaign = get_object_or_404(
                campaigns.exclude(status=Campaign.Status.COMPLETED), pk=pk
            )
            campaign.memberships.get_or_create(player=request.user)
        else:
            campaign = get_object_or_404(campaigns, pk=pk)
            campaign.memberships.filter(player=request.user).delete()
        return redirect(campaign)


class MembershipUpdateView(OwnerRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """A player chooses the character for the campaign."""

    model = CampaignMembership
    form_class = MembershipForm
    owner_field = "player"
    success_message = "Your character of the campaign was saved."
