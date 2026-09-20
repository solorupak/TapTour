from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from apps.content.models import Collection, Stop, StopTranslation
from apps.organizations.models import Organization


@method_decorator(never_cache, name="dispatch")
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizations = Organization.objects.filter(is_active=True, archived_at__isnull=True)
        if not self.request.user.is_superuser:
            organizations = organizations.filter(memberships__user=self.request.user, memberships__is_active=True)
        organizations = organizations.order_by("name")
        selected = self.request.GET.get("organization", "")
        if selected:
            # Slugs avoid accepting arbitrary primary-key input and are checked against access.
            organization = get_object_or_404(organizations, slug=selected)
        else:
            organization = organizations.first()
        collections = Collection.objects.filter(organization=organization, archived_at__isnull=True)
        stops = Stop.objects.filter(organization=organization, archived_at__isnull=True, collection__archived_at__isnull=True)
        translations = StopTranslation.objects.filter(stop__in=stops, organization=organization)
        published = translations.filter(published_revision__isnull=False)
        stats = {
            "collections": collections.count(), "stops": stops.count(),
            "published": published.count(),
            "unpublished": translations.filter(published_revision__isnull=True).count(),
        }
        query = self.request.GET.get("q", "").strip()[:200]
        if query:
            collections = collections.filter(internal_name__icontains=query)
        collections = collections.annotate(stop_count=Count("stops", filter=Q(stops__archived_at__isnull=True))).order_by("-updated_at", "pk")
        page = Paginator(collections, 8).get_page(self.request.GET.get("page"))
        context.update({
            "organizations": organizations, "organization": organization,
            "stats": stats, "page_obj": page, "query": query,
        })
        return context
