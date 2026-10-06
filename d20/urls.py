from django.urls import path

from d20.views import (
    CampaignCreateView,
    CampaignDeleteView,
    CampaignDetailView,
    CampaignListView,
    CampaignUpdateView,
    CharacterCreateView,
    CharacterDeleteView,
    CharacterDetailView,
    CharacterListView,
    CharacterUpdateView,
    GameSessionCreateView,
    GameSessionDeleteView,
    GameSessionDetailView,
    GameSessionListView,
    GameSessionUpdateView,
    ProfileUpdateView,
    UserDetailView,
)

app_name = "d20"

urlpatterns = [
    path("players/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path(
        "profile/update/", ProfileUpdateView.as_view(), name="profile-update"
    ),
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
    path(
        "campaigns/<int:pk>/sessions/create/",
        GameSessionCreateView.as_view(),
        name="session-create",
    ),
    path("characters/", CharacterListView.as_view(), name="character-list"),
    path(
        "characters/create/",
        CharacterCreateView.as_view(),
        name="character-create",
    ),
    path(
        "characters/<int:pk>/",
        CharacterDetailView.as_view(),
        name="character-detail",
    ),
    path(
        "characters/<int:pk>/update/",
        CharacterUpdateView.as_view(),
        name="character-update",
    ),
    path(
        "characters/<int:pk>/delete/",
        CharacterDeleteView.as_view(),
        name="character-delete",
    ),
    path("sessions/", GameSessionListView.as_view(), name="session-list"),
    path(
        "sessions/<int:pk>/",
        GameSessionDetailView.as_view(),
        name="session-detail",
    ),
    path(
        "sessions/<int:pk>/update/",
        GameSessionUpdateView.as_view(),
        name="session-update",
    ),
    path(
        "sessions/<int:pk>/delete/",
        GameSessionDeleteView.as_view(),
        name="session-delete",
    ),
]
