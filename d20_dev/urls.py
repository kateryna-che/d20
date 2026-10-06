from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from d20.views.users import RegisterView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("d20.urls", namespace="d20")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", RegisterView.as_view(), name="register"),
]
