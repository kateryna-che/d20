from operator import attrgetter
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Exists, OuterRef, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from d20.forms import CampaignForm, MembershipForm
from d20.models import Campaign, CampaignMembership, GameSession
from d20.views.mixins import (
    AuthenticatedHttpRequest,
    OwnerRequiredMixin,
    ReturnUrlMixin,
    SearchMixin,
)


class CampaignListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    request: AuthenticatedHttpRequest
    queryset = (
        Campaign.objects.select_related("game_master")
        .annotate(
            players_count=Count("memberships", distinct=True),
            sessions_count=Count("game_sessions", distinct=True),
        )
        .order_by("-created_at")
    )
    paginate_by = 6
    search_placeholder = "Campaign title…"

    def get_queryset(self) -> QuerySet[Campaign]:
        own_memberships = CampaignMembership.objects.filter(
            campaign=OuterRef("pk"), player=self.request.user
        )
        campaigns: QuerySet[Campaign] = super().get_queryset()
        return campaigns.annotate(is_player=Exists(own_memberships))


class CampaignDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Campaign.objects.select_related("game_master").prefetch_related(
        "memberships__player", "memberships__character", "game_sessions"
    )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["is_game_master"] = self.object.game_master_id == self.request.user.pk
        context["is_player"] = any(
            membership.player_id == self.request.user.pk
            for membership in self.object.memberships.all()
        )
        if context["is_game_master"] or context["is_player"]:
            context["notes"] = self.object.notes.select_related("author")
        context["session_groups"] = self.get_session_groups()
        return context

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
    model = Campaign
    form_class = CampaignForm
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was created. You are its game master."

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.game_master = self.request.user
        return super().form_valid(form)


class CampaignUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    model = Campaign
    form_class = CampaignForm
    success_message = "The campaign was updated."


class CampaignDeleteView(OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = Campaign
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was deleted."


@require_POST
def update_campaign_membership(request: HttpRequest, pk: int) -> HttpResponse:
    """Join or leave the campaign according to the submitted action.

    The game master runs the campaign and is not on its player list.
    """
    if not request.user.is_authenticated:
        return redirect_to_login(reverse("d20:campaign-detail", kwargs={"pk": pk}))

    action = request.POST.get("action")
    if action not in ("join", "leave"):
        return HttpResponseBadRequest("Invalid membership action.")

    campaign = get_object_or_404(
        Campaign.objects.exclude(game_master=request.user), pk=pk
    )
    if action == "join":
        campaign.memberships.get_or_create(player=request.user)
    else:
        campaign.memberships.filter(player=request.user).delete()
    return redirect(campaign)


class MembershipUpdateView(OwnerRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """A player chooses the character for the campaign."""

    model = CampaignMembership
    form_class = MembershipForm
    owner_field = "player"
    success_message = "Your character of the campaign was saved."
