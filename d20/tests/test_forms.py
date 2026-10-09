from django.forms import ModelChoiceField
from django.test import TestCase

from d20.forms import MembershipForm, RegistrationForm, SearchForm
from d20.models import Campaign, CampaignMembership
from d20.tests.utils import REGISTRATION_DATA, create_character, create_user


class FormsTests(TestCase):
    def test_registration_form_with_first_last_name_email_is_valid(self) -> None:
        form = RegistrationForm(data=REGISTRATION_DATA)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, REGISTRATION_DATA)

    def test_search_form_is_valid_with_and_without_search_value(self) -> None:
        for data in ({"search": "test"}, {}):
            with self.subTest(data=data):
                self.assertTrue(SearchForm(data=data).is_valid())

    def test_search_form_placeholder_belongs_to_its_instance(self) -> None:
        form = SearchForm(placeholder="Campaign title…")

        self.assertEqual(
            form.fields["search"].widget.attrs["placeholder"], "Campaign title…"
        )
        self.assertEqual(
            SearchForm().fields["search"].widget.attrs["placeholder"], "Search"
        )

    def test_membership_form_offers_only_player_characters(self) -> None:
        game_master = create_user("master")
        player = create_user("player")
        character = create_character(player)
        create_character(game_master, name="Legolas")
        membership = CampaignMembership.objects.create(
            campaign=Campaign.objects.create(
                title="Lost Mine", game_master=game_master
            ),
            player=player,
        )

        form = MembershipForm(instance=membership)

        character_field = form.fields["character"]
        assert isinstance(character_field, ModelChoiceField)
        assert character_field.queryset is not None
        self.assertEqual(list(character_field.queryset), [character])
