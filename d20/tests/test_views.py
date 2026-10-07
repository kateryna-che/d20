from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from d20.models import (
    Campaign,
    CampaignMembership,
    Character,
    GameSession,
    SessionParticipation,
)
from d20.tests.utils import REGISTRATION_DATA, create_character, create_user

INDEX_URL = reverse("d20:index")
CAMPAIGN_LIST_URL = reverse("d20:campaign-list")
CHARACTER_LIST_URL = reverse("d20:character-list")
SESSION_LIST_URL = reverse("d20:session-list")


class PublicViewsTests(TestCase):
    def test_login_required(self) -> None:
        for url in (
            INDEX_URL,
            CAMPAIGN_LIST_URL,
            CHARACTER_LIST_URL,
            SESSION_LIST_URL,
        ):
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertRedirects(res, f"/accounts/login/?next={url}")

    def test_register_user(self) -> None:
        res = self.client.post(reverse("register"), REGISTRATION_DATA)
        new_user = get_user_model().objects.get(username=REGISTRATION_DATA["username"])

        self.assertRedirects(res, reverse("login"))
        self.assertEqual(new_user.first_name, REGISTRATION_DATA["first_name"])
        self.assertEqual(new_user.last_name, REGISTRATION_DATA["last_name"])
        self.assertEqual(new_user.email, REGISTRATION_DATA["email"])


class PrivateIndexTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user("test")
        self.client.force_login(self.user)

    def test_index_counters(self) -> None:
        campaign = Campaign.objects.create(title="Lost Mine", game_master=self.user)
        game_session = GameSession.objects.create(
            campaign=campaign,
            title="Session 1",
            scheduled_at=timezone.now() + timedelta(days=1),
        )
        create_character(self.user)

        res = self.client.get(INDEX_URL)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "d20/index.html")
        self.assertEqual(res.context["num_campaigns"], 1)
        self.assertEqual(res.context["num_sessions"], 1)
        self.assertEqual(res.context["num_characters"], 1)
        self.assertEqual(res.context["next_session"], game_session)


class PrivateCampaignTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user("test")
        self.client.force_login(self.user)
        self.other_user = create_user("other")
        self.campaign = Campaign.objects.create(
            title="Curse of Strahd", game_master=self.user
        )
        self.other_campaign = Campaign.objects.create(
            title="Lost Mine", game_master=self.other_user
        )
        Campaign.objects.create(title="Lost Caverns", game_master=self.other_user)

    def test_retrieve_campaigns(self) -> None:
        res = self.client.get(CAMPAIGN_LIST_URL)

        self.assertEqual(res.status_code, 200)
        self.assertCountEqual(res.context["campaign_list"], Campaign.objects.all())
        self.assertTemplateUsed(res, "d20/campaign_list.html")

    def test_search_campaigns_by_title(self) -> None:
        res = self.client.get(CAMPAIGN_LIST_URL, {"search": "LOST"})

        self.assertCountEqual(
            res.context["campaign_list"],
            Campaign.objects.filter(title__icontains="lost"),
        )
        self.assertEqual(len(res.context["campaign_list"]), 2)
        self.assertNotContains(res, "Curse of Strahd")

    def test_create_campaign(self) -> None:
        res = self.client.post(
            reverse("d20:campaign-create"),
            {"title": "Tomb of Horrors", "status": Campaign.Status.PLANNING},
        )
        campaign = Campaign.objects.get(title="Tomb of Horrors")

        self.assertRedirects(res, CAMPAIGN_LIST_URL)
        self.assertEqual(campaign.game_master, self.user)

    def test_update_campaign(self) -> None:
        res = self.client.post(
            reverse("d20:campaign-update", args=[self.campaign.id]),
            {"title": "Curse of Strahd", "status": Campaign.Status.ACTIVE},
        )
        self.campaign.refresh_from_db()

        self.assertRedirects(res, self.campaign.get_absolute_url())
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)

    def test_update_campaign_of_other_game_master(self) -> None:
        res = self.client.post(
            reverse("d20:campaign-update", args=[self.other_campaign.id]),
            {"title": "Hacked", "status": Campaign.Status.ACTIVE},
        )
        self.other_campaign.refresh_from_db()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(self.other_campaign.title, "Lost Mine")

    def test_delete_campaign(self) -> None:
        res = self.client.post(reverse("d20:campaign-delete", args=[self.campaign.id]))

        self.assertRedirects(res, CAMPAIGN_LIST_URL)
        self.assertFalse(Campaign.objects.filter(id=self.campaign.id).exists())

    def test_join_and_leave_campaign(self) -> None:
        url = reverse("d20:campaign-membership", args=[self.other_campaign.id])

        res = self.client.post(url, {"action": "join"})

        self.assertRedirects(res, self.other_campaign.get_absolute_url())
        self.assertIn(self.other_campaign, self.user.campaigns.all())

        self.client.post(url, {"action": "leave"})

        self.assertNotIn(self.other_campaign, self.user.campaigns.all())

    def test_campaign_detail_groups_sessions_by_status(self) -> None:
        now = timezone.now()
        later = GameSession.objects.create(
            campaign=self.campaign,
            title="Later",
            scheduled_at=now + timedelta(days=7),
        )
        sooner = GameSession.objects.create(
            campaign=self.campaign,
            title="Sooner",
            scheduled_at=now + timedelta(days=1),
        )
        played = GameSession.objects.create(
            campaign=self.campaign,
            title="Played",
            scheduled_at=now - timedelta(days=7),
            status=GameSession.Status.COMPLETED,
        )

        res = self.client.get(self.campaign.get_absolute_url())

        self.assertEqual(
            res.context["session_groups"],
            [("Scheduled", [sooner, later]), ("Completed", [played])],
        )


class PrivateCharacterTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user("test")
        self.client.force_login(self.user)
        self.character = create_character(self.user)
        create_character(create_user("other"), name="Legolas")

    def test_retrieve_only_own_characters(self) -> None:
        res = self.client.get(CHARACTER_LIST_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["character_list"]), [self.character])
        self.assertTemplateUsed(res, "d20/character_list.html")
        self.assertNotContains(res, "Legolas")

    def test_create_character(self) -> None:
        res = self.client.post(
            reverse("d20:character-create"),
            {
                "name": "Aragorn",
                "character_class": Character.CharacterClass.RANGER,
                "ancestry": Character.Ancestry.HUMAN,
                "level": 5,
                **dict.fromkeys(Character.ABILITIES, 12),
                "max_hit_points": 40,
                "hit_points": 40,
                "armor_class": 15,
                "speed": 30,
            },
        )
        character = Character.objects.get(name="Aragorn")

        self.assertRedirects(res, CHARACTER_LIST_URL)
        self.assertEqual(character.owner, self.user)

    def test_character_detail_lists_answers_of_player(self) -> None:
        campaign = Campaign.objects.create(
            title="Lost Mine", game_master=create_user("master")
        )
        membership = CampaignMembership.objects.create(
            campaign=campaign, player=self.user, character=self.character
        )
        participation = SessionParticipation.objects.create(
            game_session=GameSession.objects.create(
                campaign=campaign,
                title="Session 1",
                scheduled_at=timezone.now() + timedelta(days=1),
            ),
            membership=membership,
        )

        res = self.client.get(self.character.get_absolute_url())

        self.assertEqual(res.context["participations"], [participation])


class PrivateGameSessionTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user("test")
        self.client.force_login(self.user)
        campaign = Campaign.objects.create(
            title="Lost Mine", game_master=create_user("master")
        )
        self.membership = CampaignMembership.objects.create(
            campaign=campaign, player=self.user
        )
        self.game_session = GameSession.objects.create(
            campaign=campaign,
            title="Session 1",
            scheduled_at=timezone.now() + timedelta(days=1),
        )

    def test_respond_to_session(self) -> None:
        res = self.client.post(
            reverse("d20:session-respond", args=[self.game_session.id]),
            {"attendance_status": SessionParticipation.Attendance.DECLINED},
        )
        participation = SessionParticipation.objects.get(
            game_session=self.game_session, membership=self.membership
        )

        self.assertRedirects(res, self.game_session.get_absolute_url())
        self.assertEqual(
            participation.attendance_status,
            SessionParticipation.Attendance.DECLINED,
        )

    def test_session_detail_lists_confirmed_characters(self) -> None:
        self.membership.character = create_character(self.user)
        self.membership.save()
        participation = SessionParticipation.objects.create(
            game_session=self.game_session, membership=self.membership
        )

        res = self.client.get(self.game_session.get_absolute_url())

        self.assertTrue(res.context["can_respond"])
        self.assertEqual(res.context["confirmed_participations"], [participation])

    def test_completed_session_accepts_no_answers(self) -> None:
        self.game_session.status = GameSession.Status.COMPLETED
        self.game_session.save()

        res = self.client.get(self.game_session.get_absolute_url())

        self.assertFalse(res.context["can_respond"])
