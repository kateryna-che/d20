from typing import Self

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    def get_absolute_url(self) -> str:
        return reverse("d20:user-detail", kwargs={"pk": self.pk})

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username


class Character(models.Model):
    class CharacterClass(models.TextChoices):
        ARTIFICER = "artificer", "Artificer"
        BARBARIAN = "barbarian", "Barbarian"
        BARD = "bard", "Bard"
        CLERIC = "cleric", "Cleric"
        DRUID = "druid", "Druid"
        FIGHTER = "fighter", "Fighter"
        MONK = "monk", "Monk"
        PALADIN = "paladin", "Paladin"
        RANGER = "ranger", "Ranger"
        ROGUE = "rogue", "Rogue"
        SORCERER = "sorcerer", "Sorcerer"
        WARLOCK = "warlock", "Warlock"
        WIZARD = "wizard", "Wizard"

    class Ancestry(models.TextChoices):
        DRAGONBORN = "dragonborn", "Dragonborn"
        DWARF = "dwarf", "Dwarf"
        ELF = "elf", "Elf"
        GNOME = "gnome", "Gnome"
        HALF_ELF = "half-elf", "Half-Elf"
        HALF_ORC = "half-orc", "Half-Orc"
        HALFLING = "halfling", "Halfling"
        HUMAN = "human", "Human"
        TIEFLING = "tiefling", "Tiefling"

    ABILITIES = (
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    )
    LEVEL_VALIDATORS = [MinValueValidator(1), MaxValueValidator(20)]
    ABILITY_VALIDATORS = [MinValueValidator(1), MaxValueValidator(30)]

    name = models.CharField(max_length=255)
    concept = models.CharField(
        max_length=255,
        blank=True,
        help_text="One line: who the hero is and what makes them memorable.",
    )
    character_class = models.CharField(
        max_length=20,
        choices=CharacterClass,
        verbose_name="class",
    )
    ancestry = models.CharField(max_length=20, choices=Ancestry)
    level = models.PositiveSmallIntegerField(default=1, validators=LEVEL_VALIDATORS)
    strength = models.PositiveSmallIntegerField(
        default=10, validators=ABILITY_VALIDATORS
    )
    dexterity = models.PositiveSmallIntegerField(
        default=10, validators=ABILITY_VALIDATORS
    )
    constitution = models.PositiveSmallIntegerField(
        default=10, validators=ABILITY_VALIDATORS
    )
    intelligence = models.PositiveSmallIntegerField(
        default=10, validators=ABILITY_VALIDATORS
    )
    wisdom = models.PositiveSmallIntegerField(default=10, validators=ABILITY_VALIDATORS)
    charisma = models.PositiveSmallIntegerField(
        default=10, validators=ABILITY_VALIDATORS
    )
    max_hit_points = models.PositiveSmallIntegerField(
        default=10, verbose_name="maximum hit points"
    )
    hit_points = models.PositiveSmallIntegerField(
        default=10, verbose_name="current hit points"
    )
    armor_class = models.PositiveSmallIntegerField(default=10)
    speed = models.PositiveSmallIntegerField(default=30, verbose_name="speed, ft.")
    abilities = models.TextField(
        blank=True,
        help_text="Features, traits and spells: one entry per line.",
    )
    inventory = models.TextField(blank=True, help_text="One item per line.")
    notes = models.TextField(blank=True, verbose_name="sheet notes")
    backstory = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="characters",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("d20:character-detail", kwargs={"pk": self.pk})

    @property
    def summary(self) -> str:
        """Short line such as "Level 3 Elf Wizard"."""
        return (
            f"Level {self.level} {self.get_ancestry_display()} "
            f"{self.get_character_class_display()}"
        )

    @property
    def stat_blocks(self) -> list[dict[str, str | int]]:
        """Ability scores with the modifiers that are added to dice rolls."""
        return [
            {
                "label": ability.capitalize(),
                "score": getattr(self, ability),
                "modifier": (getattr(self, ability) - 10) // 2,
            }
            for ability in self.ABILITIES
        ]


class CampaignQuerySet(models.QuerySet):
    def for_user(self, user: User) -> Self:
        """Campaigns that the user runs or plays in."""
        return self.filter(
            models.Q(game_master=user) | models.Q(players=user)
        ).distinct()


class Campaign(models.Model):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.PLANNING)
    game_master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mastered_campaigns",
    )
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CampaignMembership",
        related_name="campaigns",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CampaignQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("d20:campaign-detail", kwargs={"pk": self.pk})


class CampaignMembership(models.Model):
    """A player of a campaign and the character the player brings to it."""

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="memberships"
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    character = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "player"], name="unique_campaign_player"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.player} in {self.campaign}"

    def get_absolute_url(self) -> str:
        return reverse("d20:campaign-detail", kwargs={"pk": self.campaign_id})

    def clean(self) -> None:
        super().clean()
        if self.player_id is None:
            return

        if self.campaign_id is not None:
            try:
                campaign = self.campaign
            except Campaign.DoesNotExist:
                return

            if campaign.game_master_id == self.player_id:
                raise ValidationError(
                    "The game master runs the campaign and cannot be its player."
                )

        try:
            character = self.character
        except Character.DoesNotExist:
            return

        if character is not None and character.owner_id != self.player_id:
            raise ValidationError(
                {"character": "The character must belong to the campaign player."}
            )


class GameSession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="game_sessions"
    )
    title = models.CharField(max_length=255)
    scheduled_at = models.DateTimeField(verbose_name="date and time")
    play_location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="place or link",
        help_text="An address, a club name or a link to the online room.",
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.SCHEDULED)
    agenda = models.TextField(blank=True)
    summary = models.TextField(
        blank=True,
        help_text="Filled in after the game: what happened and how it ended.",
    )

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("d20:session-detail", kwargs={"pk": self.pk})

    @property
    def location_is_link(self) -> bool:
        return self.play_location.startswith(("http://", "https://"))


class SessionParticipation(models.Model):
    """The answer of a campaign player to one game session."""

    class Attendance(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        DECLINED = "declined", "Declined"

    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name="participations"
    )
    membership = models.ForeignKey(
        CampaignMembership,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    attendance_status = models.CharField(
        max_length=20, choices=Attendance, default=Attendance.CONFIRMED
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game_session", "membership"],
                name="unique_session_membership",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.membership.player} at {self.game_session}"

    def clean(self) -> None:
        super().clean()
        if self.game_session_id is None or self.membership_id is None:
            return

        try:
            game_session = self.game_session
            membership = self.membership
        except (GameSession.DoesNotExist, CampaignMembership.DoesNotExist):
            return

        if membership.campaign_id != game_session.campaign_id:
            raise ValidationError(
                {"membership": "The player must belong to the session's campaign."}
            )


class PreparationNote(models.Model):
    class Kind(models.TextChoices):
        GENERAL = "general", "General"
        NPC = "npc", "NPC"
        LOCATION = "location", "Location"
        QUEST = "quest", "Quest"
        ITEM = "item", "Item"
        RESOURCE = "resource", "Resource"

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=Kind, default=Kind.GENERAL)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("d20:note-detail", kwargs={"pk": self.pk})
