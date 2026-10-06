from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from d20.forms import CampaignForm, MembershipForm
from d20.models import Campaign, CampaignMembership
from d20.views.mixins import OwnerRequiredMixin, ReturnUrlMixin, SearchMixin


class CampaignListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    queryset = (
        Campaign.objects.select_related("game_master")
        .annotate(
            players_count=Count("memberships", distinct=True),
            sessions_count=Count("game_sessions", distinct=True),
        )
        .order_by("-created_at")
    )
    paginate_by = 6


class CampaignDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Campaign.objects.select_related("game_master").prefetch_related(
        "memberships__player", "memberships__character", "game_sessions"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_game_master"] = self.object.game_master_id == self.request.user.pk
        context["is_player"] = any(
            membership.player_id == self.request.user.pk
            for membership in self.object.memberships.all()
        )
        return context


class CampaignCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    model = Campaign
    form_class = CampaignForm
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was created. You are its game master."

    def form_valid(self, form):
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
def update_campaign_membership(request, pk):
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
