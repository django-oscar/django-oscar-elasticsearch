import doctest

from time import sleep
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from oscar.core.loading import get_class, get_model

import oscar_elasticsearch.search.format
import oscar_elasticsearch.search.utils

Product = get_model("catalogue", "Product")
update_index_products = get_class("search.helpers", "update_index_products")


def load_tests(loader, tests, ignore):  # pylint: disable=W0613
    tests.addTests(doctest.DocTestSuite(oscar_elasticsearch.search.format))
    tests.addTests(doctest.DocTestSuite(oscar_elasticsearch.search.utils))
    return tests


class ElasticSearchViewTest(TestCase):
    fixtures = [
        "search/auth",
        "catalogue/catalogue",
    ]

    @classmethod
    def setUpClass(cls):
        # clear search index
        call_command("update_oscar_index")
        super().setUpClass()

    def setUp(self):
        super().setUp()
        update_index_products(Product.objects.values_list("id", flat=True))
        sleep(3)

    def test_search_bikini(self):
        url = reverse("search:search")
        response = self.client.get("%s?q=bikini" % url)
        self.assertContains(response, "Hermes Bikini")

    def test_search_suggestion(self):
        url = reverse("search:search")
        response = self.client.get("%s?q=prods" % url)
        self.assertEqual(response.context["suggestion"], "produ")

    def test_browse(self):
        url = reverse("catalogue:index")
        response = self.client.get(url)
        self.assertContains(response, "second")
        self.assertContains(response, "serious product")
        self.assertContains(response, "Hubble Photo")
        self.assertContains(response, "Hermes Bikini")

    def test_catagory(self):
        url = reverse("catalogue:category", args=("root", 1))
        response = self.client.get(url)
        self.assertContains(response, "second")
        self.assertContains(response, "serious product")
        self.assertContains(response, "Hubble Photo")
        self.assertContains(response, "Hermes Bikini")

    def test_no_stockrecord_and_not_public(self):
        self.test_catagory()

        hubble = Product.objects.get(pk=3)
        hubble.is_public = False
        hubble.save()

        update_index_products([hubble.pk])
        sleep(2)

        url = reverse("catalogue:category", args=("root", 1))
        response = self.client.get(url)
        self.assertContains(response, "second")
        self.assertContains(response, "serious product")
        self.assertNotContains(response, "Hubble Photo")
