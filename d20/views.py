from urllib.parse import urlsplit

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic

from d20.forms import CampaignForm, GameSessionForm
from d20.models import Campaign, GameSession


class OwnerRequiredMixin(LoginRequiredMixin):
    owner_field = "game_master"

    def get_queryset(self):
        return super().get_queryset().filter(**{self.owner_field: self.request.user})


class ReturnUrlMixin:
    """Keep the source page through form submission and validation errors."""

    def get_return_url(self):
        if self.request.method == "POST":
            return_url = self.request.POST.get("next", "")
        else:
            return_url = self.request.GET.get("next") or self.request.META.get(
                "HTTP_REFERER", ""
            )

        if (
            url_has_allowed_host_and_scheme(
                return_url,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            )
            and urlsplit(return_url).path != self.request.path
        ):
            return return_url
        return self.get_default_return_url()

    def get_default_return_url(self):
        return str(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.get_return_url()
        return context

    def get_success_url(self):
        return self.get_return_url()


def get_user_campaigns(user):
    """Campaigns that the user runs or plays in."""
    return Campaign.objects.filter(Q(game_master=user) | Q(players=user)).distinct()


class CampaignListView(LoginRequiredMixin, generic.ListView):
    queryset = (
        Campaign.objects.select_related("game_master")
        .prefetch_related("players")
        .annotate(sessions_count=Count("game_sessions", distinct=True))
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

    def get_default_return_url(self):
        return reverse("d20:campaign-detail", kwargs={"pk": self.object.pk})


class CampaignDeleteView(OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = Campaign
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was deleted."


class GameSessionListView(LoginRequiredMixin, generic.ListView):
    """Sessions of the campaigns that the user runs or plays in.

    Sessions of other campaigns are opened from campaign pages.
    """

    queryset = (
        GameSession.objects.select_related("campaign")
        .annotate(answers_count=Count("participations"))
        .order_by("-scheduled_at")
    )
    paginate_by = 8

    def get_queryset(self):
        campaigns = get_user_campaigns(self.request.user)
        return super().get_queryset().filter(campaign__in=campaigns)


class GameSessionDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = GameSession.objects.select_related(
        "campaign__game_master"
    ).prefetch_related(
        "participations__membership__player",
        "participations__membership__character",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_participation"] = self.object.participations.filter(
            membership__player=self.request.user
        ).first()
        context["is_game_master"] = (
            self.object.campaign.game_master_id == self.request.user.pk
        )
        return context


class GameSessionCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    """The game master plans a session of the campaign from the URL."""

    model = GameSession
    form_class = GameSessionForm
    success_message = "The session was planned."

    def get_campaign(self):
        return get_object_or_404(
            Campaign, pk=self.kwargs["pk"], game_master=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.get_campaign()
        return context

    def form_valid(self, form):
        form.instance.campaign = self.get_campaign()
        return super().form_valid(form)

    def get_default_return_url(self):
        return reverse("d20:campaign-detail", kwargs={"pk": self.kwargs["pk"]})


class GameSessionUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    model = GameSession
    form_class = GameSessionForm
    owner_field = "campaign__game_master"
    success_message = "The session was updated."

    def get_default_return_url(self):
        return reverse("d20:session-detail", kwargs={"pk": self.object.pk})


class GameSessionDeleteView(
    OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
    model = GameSession
    owner_field = "campaign__game_master"
    success_url = reverse_lazy("d20:session-list")
    success_message = "The session was deleted."
