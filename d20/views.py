from urllib.parse import urlsplit

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic
from django.views.decorators.http import require_POST

from d20.forms import (
    CampaignForm,
    GameSessionForm,
    CharacterForm,
    ProfileForm,
    MembershipForm,
    PreparationNoteForm,
    ParticipationForm,
    SearchForm,
)
from d20.models import (
    Campaign,
    GameSession,
    Character,
    CampaignMembership,
    PreparationNote,
    SessionParticipation,
)


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
            return_url = self.request.GET.get("next", "")

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
        if self.success_url:
            return str(self.success_url)
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.get_return_url()
        return context

    def get_success_url(self):
        return self.get_return_url()


class SearchMixin:
    """Filter a list by a validated search term and keep its form in context."""

    search_field = "title"

    def get_queryset(self):
        queryset = super().get_queryset()
        self.search_form = SearchForm(self.request.GET)
        self.search_query = ""
        if self.search_form.is_valid():
            self.search_query = self.search_form.cleaned_data["search"]
            if self.search_query:
                queryset = queryset.filter(
                    **{f"{self.search_field}__icontains": self.search_query}
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        context["search_query"] = self.search_query
        return context


def get_user_campaigns(user):
    """Campaigns that the user runs or plays in."""
    return Campaign.objects.filter(Q(game_master=user) | Q(players=user)).distinct()


@login_required
@require_POST
def update_campaign_membership(request, pk):
    """Join or leave the campaign according to the submitted action.

    The game master runs the campaign and is not on its player list.
    """
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


@login_required
@require_POST
def respond_to_session(request, pk):
    """Save the answer of a campaign player: confirmed or declined.

    Only a scheduled session accepts answers.
    """
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


class UserDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = get_user_model().objects.prefetch_related(
        "characters",
        "mastered_campaigns",
        "memberships__campaign__game_master",
        "memberships__character",
    )
    context_object_name = "profile"


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    form_class = ProfileForm
    template_name = "d20/user_form.html"
    context_object_name = "profile"
    success_message = "Your profile was updated."

    def get_object(self, queryset=None):
        return get_user_model().objects.get(pk=self.request.user.pk)

    def get_success_url(self):
        return reverse("d20:user-detail", kwargs={"pk": self.object.pk})


class CampaignListView(LoginRequiredMixin, SearchMixin, generic.ListView):
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


class MembershipUpdateView(OwnerRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """A player chooses the character for the campaign."""

    model = CampaignMembership
    form_class = MembershipForm
    owner_field = "player"
    success_message = "Your character of the campaign was saved."

    def get_success_url(self):
        return self.object.campaign.get_absolute_url()


class CharacterListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    """The characters of the logged-in user.

    Characters of other players are opened from campaign pages.
    """

    model = Character
    paginate_by = 8
    search_field = "name"

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class CharacterDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = Character.objects.select_related("owner").prefetch_related(
        "memberships__campaign",
        "memberships__participations__game_session",
    )


class CharacterCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    model = Character
    form_class = CharacterForm
    success_url = reverse_lazy("d20:character-list")
    success_message = "The character was created."

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CharacterUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    model = Character
    form_class = CharacterForm
    owner_field = "owner"
    success_message = "The character sheet was saved."


class CharacterDeleteView(OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = Character
    owner_field = "owner"
    success_url = reverse_lazy("d20:character-list")
    success_message = "The character was deleted."


class GameSessionListView(LoginRequiredMixin, SearchMixin, generic.ListView):
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


class GameSessionDeleteView(
    OwnerRequiredMixin, SuccessMessageMixin, generic.DeleteView
):
    model = GameSession
    owner_field = "campaign__game_master"
    success_url = reverse_lazy("d20:session-list")
    success_message = "The session was deleted."


class PreparationNoteDetailView(LoginRequiredMixin, generic.DetailView):
    """A note is open to the game master and the players of its campaign."""

    queryset = PreparationNote.objects.select_related("campaign", "author")

    def get_queryset(self):
        campaigns = get_user_campaigns(self.request.user)
        return super().get_queryset().filter(campaign__in=campaigns)


class PreparationNoteCreateView(
    LoginRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.CreateView
):
    """The game master or a player adds a note to the campaign from the URL."""

    model = PreparationNote
    form_class = PreparationNoteForm
    success_message = "The note was added."

    def get_campaign(self):
        return get_object_or_404(
            get_user_campaigns(self.request.user), pk=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.get_campaign()
        return context

    def form_valid(self, form):
        form.instance.campaign = self.get_campaign()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_default_return_url(self):
        return reverse("d20:campaign-detail", kwargs={"pk": self.kwargs["pk"]})


class PreparationNoteUpdateView(
    OwnerRequiredMixin, ReturnUrlMixin, SuccessMessageMixin, generic.UpdateView
):
    """The author edits the note while in its campaign."""

    model = PreparationNote
    form_class = PreparationNoteForm
    owner_field = "author"
    success_message = "The note was saved."

    def get_queryset(self):
        campaigns = get_user_campaigns(self.request.user)
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
                campaign__in=get_user_campaigns(user),
            )
        )

    def get_success_url(self):
        return self.object.campaign.get_absolute_url()
