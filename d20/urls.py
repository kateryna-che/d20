from django.urls import path
from django.views.generic import TemplateView

from d20.views.campaigns import (
    CampaignCreateView,
    CampaignDeleteView,
    CampaignDetailView,
    CampaignListView,
    CampaignUpdateView,
    MembershipUpdateView,
    update_campaign_membership,
)
from d20.views.characters import (
    CharacterCreateView,
    CharacterDeleteView,
    CharacterDetailView,
    CharacterListView,
    CharacterUpdateView,
)
from d20.views.game_sessions import (
    GameSessionCreateView,
    GameSessionDeleteView,
    GameSessionDetailView,
    GameSessionListView,
    GameSessionUpdateView,
    respond_to_session,
)
from d20.views.home import index
from d20.views.notes import (
    PreparationNoteCreateView,
    PreparationNoteDeleteView,
    PreparationNoteDetailView,
    PreparationNoteUpdateView,
)
from d20.views.users import ProfileUpdateView, UserDetailView

app_name = "d20"

urlpatterns = [
    path("", index, name="index"),
    path("about/", TemplateView.as_view(template_name="d20/about.html"), name="about"),
    path("players/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
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
        "campaigns/<int:pk>/membership/",
        update_campaign_membership,
        name="campaign-membership",
    ),
    path(
        "memberships/<int:pk>/update/",
        MembershipUpdateView.as_view(),
        name="membership-update",
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
    path(
        "sessions/<int:pk>/respond/",
        respond_to_session,
        name="session-respond",
    ),
    path(
        "campaigns/<int:pk>/notes/create/",
        PreparationNoteCreateView.as_view(),
        name="note-create",
    ),
    path(
        "notes/<int:pk>/",
        PreparationNoteDetailView.as_view(),
        name="note-detail",
    ),
    path(
        "notes/<int:pk>/update/",
        PreparationNoteUpdateView.as_view(),
        name="note-update",
    ),
    path(
        "notes/<int:pk>/delete/",
        PreparationNoteDeleteView.as_view(),
        name="note-delete",
    ),
]
