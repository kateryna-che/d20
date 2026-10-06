from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from d20.models import Campaign, CampaignMembership
from d20.tests.utils import create_character, create_user


class ModelsTests(TestCase):
    def setUp(self):
        self.game_master = create_user("master")
        self.player = create_user("player")
        self.campaign = Campaign.objects.create(
            title="Lost Mine", game_master=self.game_master
        )

    def test_user_str(self):
        self.assertEqual(str(self.player), self.player.username)

    def test_character_str(self):
        character = create_character(self.player)
        self.assertEqual(str(character), character.name)

    def test_campaign_str(self):
        self.assertEqual(str(self.campaign), self.campaign.title)

    def test_create_user_with_bio(self):
        username = "test"
        password = "test123"
        bio = "Plays bards only."
        user = get_user_model().objects.create_user(
            username=username, password=password, bio=bio
        )
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.bio, bio)

    def test_user_get_absolute_url(self):
        self.assertEqual(self.player.get_absolute_url(), f"/players/{self.player.id}/")

    def test_campaigns_for_user(self):
        CampaignMembership.objects.create(campaign=self.campaign, player=self.player)
        Campaign.objects.create(title="Other", game_master=create_user("stranger"))

        for user in (self.game_master, self.player):
            with self.subTest(user=user.username):
                self.assertEqual(list(Campaign.objects.for_user(user)), [self.campaign])

    def test_game_master_cannot_be_campaign_player(self):
        membership = CampaignMembership(campaign=self.campaign, player=self.game_master)
        with self.assertRaisesMessage(ValidationError, "cannot be its player"):
            membership.full_clean()

    def test_membership_character_should_belong_to_player(self):
        membership = CampaignMembership(
            campaign=self.campaign,
            player=self.player,
            character=create_character(self.game_master),
        )
        with self.assertRaises(ValidationError) as context:
            membership.full_clean()
        self.assertIn("character", context.exception.message_dict)
