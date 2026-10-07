from datetime import timedelta
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.timesince import timeuntil
from django.views import generic

from d20.models import Campaign, GameSession
from d20.views.mixins import AuthenticatedHttpRequest

SESSION_START_GRACE = timedelta(hours=4)


class IndexView(LoginRequiredMixin, generic.TemplateView):
    """The home page of the site."""

    request: AuthenticatedHttpRequest
    template_name = "d20/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        my_campaigns = Campaign.objects.for_user(user)
        my_sessions = GameSession.objects.filter(campaign__in=my_campaigns)
        scheduled_sessions = (
            my_sessions.filter(status=GameSession.Status.SCHEDULED)
            .select_related("campaign")
            .order_by("scheduled_at", "pk")
        )
        upcoming_sessions = list(
            scheduled_sessions.filter(scheduled_at__gte=now - SESSION_START_GRACE)[:5]
        )
        next_session = upcoming_sessions[0] if upcoming_sessions else None
        unanswered_sessions = scheduled_sessions.filter(
            scheduled_at__gte=now, campaign__players=user
        ).exclude(participations__membership__player=user)
        campaigns = list(my_campaigns.select_related("game_master"))

        context.update(
            {
                "num_campaigns": len(campaigns),
                "num_sessions": my_sessions.count(),
                "num_characters": user.characters.count(),
                "my_campaigns": campaigns,
                "my_characters": user.characters.all()[:6],
                "next_session": next_session,
                "starts_in": (
                    timeuntil(next_session.scheduled_at, now, depth=1)
                    if next_session and next_session.scheduled_at > now
                    else ""
                ),
                "upcoming_sessions": upcoming_sessions,
                "unanswered_sessions": unanswered_sessions,
            }
        )
        return context
