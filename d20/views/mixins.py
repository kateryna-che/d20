from typing import Any
from urllib.parse import urlsplit

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import BaseCreateView, ModelFormMixin
from django.views.generic.list import MultipleObjectMixin

from d20.forms import SearchForm
from d20.models import Campaign, User


class AuthenticatedHttpRequest(HttpRequest):
    """A request that has passed the login check: its user is not anonymous.

    A type checker cannot know that by itself, so a view that hands the user
    of the request to a query names this type of its request.
    """

    user: User


class OwnerRequiredMixin(LoginRequiredMixin, SingleObjectMixin):
    request: HttpRequest
    owner_field = "game_master"

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(**{self.owner_field: self.request.user})


class ReturnUrlMixin(ModelFormMixin):
    """Keep the source page through form submission and validation errors."""

    request: HttpRequest
    object: Any

    def get_return_url(self) -> str:
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

    def get_default_return_url(self) -> str:
        if self.success_url:
            return str(self.success_url)
        if self.object is None:
            raise ImproperlyConfigured(
                f"{type(self).__name__} needs success_url or its own "
                "get_default_return_url()."
            )
        return str(self.object.get_absolute_url())

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["next"] = self.get_return_url()
        return context

    def get_success_url(self) -> str:
        return self.get_return_url()


class CampaignRelatedCreateMixin(ReturnUrlMixin, BaseCreateView):
    """Create an object in the campaign from the URL.

    The campaign is found before the form is shown or saved, so list the
    mixin after LoginRequiredMixin. The form returns to the campaign page.
    """

    def get_campaigns(self) -> QuerySet[Campaign]:
        """Campaigns that the user may add the object to."""
        raise NotImplementedError

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.campaign = get_object_or_404(self.get_campaigns(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.campaign
        return context

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.campaign = self.campaign
        return super().form_valid(form)

    def get_default_return_url(self) -> str:
        return self.campaign.get_absolute_url()


class SearchMixin(MultipleObjectMixin):
    """Filter a list by a validated search term and keep its form in context."""

    request: HttpRequest
    search_field = "title"

    def get_queryset(self) -> QuerySet[Any]:
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        context["search_query"] = self.search_query
        return context
