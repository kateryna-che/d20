from django.urls import path

from d20.views import (
    CampaignCreateView,
    CampaignDeleteView,
    CampaignDetailView,
    CampaignListView,
    CampaignUpdateView,
)

app_name = "d20"

urlpatterns = [
    path("campaigns/", CampaignListView.as_view(), name="campaign-list"),
    path(
        "campaigns/create/",
        CampaignCreateView.as_view(),
        name="campaign-create",
    ),
    path(
        "campaigns/<int:pk>/",
        CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path(
        "campaigns/<int:pk>/update/",
        CampaignUpdateView.as_view(),
        name="campaign-update",
    ),
    path(
        "campaigns/<int:pk>/delete/",
        CampaignDeleteView.as_view(),
        name="campaign-delete",
    ),
]
