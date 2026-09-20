from django.contrib import admin
from django.urls import path

from config.health import health
from apps.accounts.views import SignInView
from apps.core.views import DashboardView
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
]
