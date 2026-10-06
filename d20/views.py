from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.views import generic

from d20.forms import CampaignForm
from d20.models import Campaign


class CampaignOwnerMixin(LoginRequiredMixin):
    queryset = Campaign.objects.all()

    def get_queryset(self):
        return self.queryset.filter(game_master=self.request.user)


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


class CampaignCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = Campaign
    form_class = CampaignForm
    success_message = "The campaign was created. You are its game master."

    def form_valid(self, form):
        form.instance.game_master = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("d20:campaign-detail", kwargs={"pk": self.object.pk})


class CampaignUpdateView(CampaignOwnerMixin, SuccessMessageMixin, generic.UpdateView):
    model = Campaign
    form_class = CampaignForm
    success_message = "The campaign was updated."

    def get_success_url(self):
        return reverse("d20:campaign-detail", kwargs={"pk": self.object.pk})


class CampaignDeleteView(CampaignOwnerMixin, SuccessMessageMixin, generic.DeleteView):
    model = Campaign
    success_url = reverse_lazy("d20:campaign-list")
    success_message = "The campaign was deleted."
