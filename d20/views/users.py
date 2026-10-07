from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views import generic

from d20.forms import ProfileForm, RegistrationForm
from d20.models import User
from d20.views.mixins import AuthenticatedHttpRequest


class RegisterView(SuccessMessageMixin, generic.CreateView):
    form_class = RegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")
    success_message = "Welcome to the table! Log in with your new account."


class UserDetailView(LoginRequiredMixin, generic.DetailView):
    queryset = get_user_model().objects.prefetch_related(
        "characters",
        "mastered_campaigns",
        "memberships__campaign__game_master",
        "memberships__character",
    )
    context_object_name = "profile"


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    request: AuthenticatedHttpRequest
    form_class = ProfileForm
    template_name = "d20/user_form.html"
    context_object_name = "profile"
    success_message = "Your profile was updated."

    def get_object(self, queryset: QuerySet[User] | None = None) -> User:
        return get_user_model().objects.get(pk=self.request.user.pk)
