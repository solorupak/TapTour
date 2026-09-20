from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Collection, Language, Stop, StopTranslation
from apps.organizations.models import Membership, Organization


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="viewer@example.com", password="password")
        cls.language = Language.objects.create(code="en", english_name="English", native_name="English")
        cls.organization = Organization.objects.create(name="Museum", slug="museum", default_language=cls.language)
        cls.other = Organization.objects.create(name="Private organization", slug="private", default_language=cls.language)
        cls.membership = Membership.objects.create(user=cls.user, organization=cls.organization, role="viewer")
        cls.collection = Collection.objects.create(organization=cls.organization, internal_name="Local history")
        Collection.objects.create(organization=cls.other, internal_name="Secret collection")
        cls.stop = Stop.objects.create(organization=cls.organization, collection=cls.collection, internal_name="The courtyard", source_language=cls.language)
        StopTranslation.objects.create(organization=cls.organization, stop=cls.stop, language=cls.language)

    def setUp(self):
        self.client.force_login(self.user)

    def test_overview_is_scoped_and_counts_real_data(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Local history")
        self.assertNotContains(response, "Secret collection")
        self.assertNotContains(response, "Private organization")
        self.assertEqual(response.context["stats"], {"collections": 1, "stops": 1, "published": 0, "unpublished": 1})
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_unassigned_organization_cannot_be_selected(self):
        for slug in ("private", "does-not-exist"):
            self.assertEqual(self.client.get(reverse("dashboard"), {"organization": slug}).status_code, 404)

    def test_staff_flag_does_not_grant_tenant_access(self):
        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get(reverse("dashboard"), {"organization": "private"}).status_code, 404)

    def test_inactive_membership_has_empty_workspace(self):
        self.membership.is_active = False
        self.membership.save()
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Your workspace is waiting")
        self.assertNotContains(response, "Local history")

    def test_inactive_and_archived_organizations_are_excluded(self):
        self.organization.is_active = False
        self.organization.save()
        self.assertContains(self.client.get(reverse("dashboard")), "Your workspace is waiting")
        self.organization.is_active = True
        self.organization.archived_at = timezone.now()
        self.organization.save()
        self.assertContains(self.client.get(reverse("dashboard")), "Your workspace is waiting")

    def test_superuser_can_select_other_organization(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertContains(self.client.get(reverse("dashboard"), {"organization": "private"}), "Secret collection")

    def test_search_and_pagination_preserve_scope(self):
        for index in range(9):
            Collection.objects.create(organization=self.organization, internal_name=f"Gallery {index}")
        response = self.client.get(reverse("dashboard"), {"q": "Gallery", "page": "2"})
        self.assertEqual(response.context["page_obj"].paginator.count, 9)
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertNotContains(response, "Local history")
        self.assertNotContains(response, "Secret collection")
        self.assertContains(self.client.get(reverse("dashboard"), {"q": "missing"}), "No collections match your search")

    def test_archived_collection_excluded_from_counts(self):
        self.collection.archived_at = timezone.now()
        self.collection.save()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["stats"], {"collections": 0, "stops": 0, "published": 0, "unpublished": 0})
