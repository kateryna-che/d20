from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from d20.tests.utils import create_user


class AdminSiteTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin", password="testadmin"
        )
        self.client.force_login(self.admin_user)
        self.player = create_user("player", bio="Plays a grumpy dwarf.")

    def test_user_detail_bio_listed(self) -> None:
        url = reverse("admin:d20_user_change", args=[self.player.id])
        res = self.client.get(url)
        self.assertContains(res, self.player.bio)
