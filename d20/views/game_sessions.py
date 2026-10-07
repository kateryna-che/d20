from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from d20.forms import GameSessionForm, ParticipationForm
from d20.models import Campaign, CampaignMembership, GameSession, SessionParticipation
from d20.views.mixins import (
    AuthenticatedHttpRequest,
    CampaignRelatedCreateMixin,
    OwnerRequiredMixin,
    ReturnUrlMixin,
    SearchMixin,
)


class GameSessionListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    """Sessions of the campaigns that the user runs or plays in.

    Sessions of other campaigns are opened from campaign pages.
    """

    request: AuthenticatedHttpRequest
    queryset = (
        GameSession.objects.select_related("campaign")
        .annotate(answers_count=Count("participations"))
        .order_by("-scheduled_at", "-pk")
    )
    paginate_by = 8

    def get_queryset(self) -> QuerySet[GameSession]:
        campaigns = Campaign.objects.for_user(self.request.user)
        return super().get_queryset().filter(campaign__in=campaigns)


class GameSessionDetailView(LoginRequiredMixin, generic.DetailView):
    request: AuthenticatedHttpRequest
    queryset = GameSession.objects.select_related(
        "campaign__game_master"
    ).prefetch_related(
        "participations__membership__player",
        "participations__membership__character",
    )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        my_participation = next(
            (
                participation
                for participation in self.object.participations.all()
                if participation.membership.player_id == self.request.user.pk
            ),
            None,
        )
        context["my_participation"] = my_participation
        context["is_game_master"] = (
            self.object.campaign.game_master_id == self.request.user.pk
        )
        context["is_player"] = (
            my_participation is not None
            or CampaignMembership.objects.filter(
                campaign_id=self.object.campaign_id, player=self.request.user
            ).exists()
        )
        context["can_respond"] = (
            context["is_player"] and self.object.status == GameSession.Status.SCHEDULED
        )
        context["confirmed_participations"] = [
            participation
            for participation in self.object.participations.all()
            if participation.attendance_status
            == SessionParticipation.Attendance.CONFIRMED
            and participation.membership.character
        ]
        return context


class GameSessionCreateView(
    LoginRequiredMixin,
    CampaignRelatedCreateMixin,
    SuccessMessageMixin,
    generic.CreateView,
):
    """The game master plans a session of the campaign from the URL."""

    request: AuthenticatedHttpRequest
    model = GameSession
    form_class = GameSessionForm
    success_message = "The session was planned."

    def get_campaigns(self) -> QuerySet[Campaign]:
        return Campaign.objects.filter(game_master=self.request.user)


class GameSessionUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    model = GameSession
    form_class = GameSessionForm
    owner_field = "campaign__game_master"
    success_message = "The session was updated."


class GameSessionDeleteView(
    OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
    model = GameSession
    owner_field = "campaign__game_master"
    success_url = reverse_lazy("d20:session-list")
    success_message = "The session was deleted."


@require_POST
def respond_to_session(request: HttpRequest, pk: int) -> HttpResponse:
    """Save the answer of a campaign player: confirmed or declined.

    Only a scheduled session accepts answers.
    """
    if not request.user.is_authenticated:
        return redirect_to_login(reverse("d20:session-detail", kwargs={"pk": pk}))

    game_session = get_object_or_404(
        GameSession, pk=pk, status=GameSession.Status.SCHEDULED
    )
    membership = get_object_or_404(
        CampaignMembership,
        campaign=game_session.campaign_id,
        player=request.user,
    )
    form = ParticipationForm(request.POST)
    if form.is_valid():
        SessionParticipation.objects.update_or_create(
            game_session=game_session,
            membership=membership,
            defaults=form.cleaned_data,
        )
    else:
        messages.error(request, "Choose a valid answer: confirmed or declined.")
    return redirect(game_session)
