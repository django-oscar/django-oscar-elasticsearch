import doctest
from unittest.mock import patch

from time import sleep
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from oscar.core.loading import get_class, get_model
from oscar.test.factories import ProductFactory

import oscar_elasticsearch.search.format
import oscar_elasticsearch.search.utils

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")

update_index_products = get_class("search.helpers", "update_index_products")
update_index_categories = get_class("search.helpers", "update_index_categories")

ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")
CategoryElasticsearchIndex = get_class(
    "search.api.category", "CategoryElasticsearchIndex"
)


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


class TestSearchApi(TestCase):
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
        update_index_categories(Category.objects.values_list("id", flat=True))
        sleep(3)

    product_search_api = ProductElasticsearchIndex()
    category_search_api = CategoryElasticsearchIndex()

    def test_product_search(self):
        results, total_hits = self.product_search_api.search()

        self.assertEqual(results.count(), 4)
        self.assertEqual(total_hits, 4)

        results, total_hits = self.product_search_api.search(query_string="bikini")

        self.assertEqual(results.count(), 1)
        self.assertEqual(total_hits, 1)

    def test_category_search(self):
        results, total_hits = self.category_search_api.search()

        self.assertEqual(results.count(), 2)
        self.assertEqual(total_hits, 2)

        results, total_hits = self.category_search_api.search(query_string="hoi")

        self.assertEqual(results.count(), 1)
        self.assertEqual(total_hits, 1)


class ManagementCommandsTestCase(TestCase):
    fixtures = [
        "search/auth",
        "catalogue/catalogue",
    ]

    def setUp(self):
        # Clear index before each test
        with ProductElasticsearchIndex().reindex() as index:
            self.product_index = index
            index.reindex_objects(Product.objects.none())

        with CategoryElasticsearchIndex().reindex() as index:
            self.category_index = index
            index.reindex_objects([])

        super().setUp()

    def test_update_index_products(self):
        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 0)
        self.assertEqual(total_hits, 0)

        call_command("update_index_products")
        sleep(3)

        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 4)
        self.assertEqual(total_hits, 4)

    @patch("oscar_elasticsearch.search.settings.INDEXING_CHUNK_SIZE", 2)
    def test_update_index_products_multiple_chunks(self):
        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 0)
        self.assertEqual(total_hits, 0)

        call_command("update_index_products")
        sleep(3)

        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 4)
        self.assertEqual(total_hits, 4)

    def test_update_index_categories(self):
        results, total_hits = self.category_index.search()
        self.assertEqual(results.count(), 0)
        self.assertEqual(total_hits, 0)

        call_command("update_index_categories")
        sleep(3)

        results, total_hits = self.category_index.search()
        self.assertEqual(results.count(), 2)
        self.assertEqual(total_hits, 2)

    @patch("oscar_elasticsearch.search.settings.INDEXING_CHUNK_SIZE", 1)
    def test_update_index_categories_multiple_chunks(self):
        results, total_hits = self.category_index.search()
        self.assertEqual(results.count(), 0)
        self.assertEqual(total_hits, 0)

        call_command("update_index_categories")
        sleep(3)

        results, total_hits = self.category_index.search()
        self.assertEqual(results.count(), 2)
        self.assertEqual(total_hits, 2)

    @patch("oscar_elasticsearch.search.settings.INDEXING_CHUNK_SIZE", 1000)
    def test_update_index_products_num_queries(self):
        def create_parent_child_products():
            for _ in range(10):
                parent = ProductFactory(
                    structure="parent",
                    stockrecords=[],
                    categories=Category.objects.all(),
                )
                for _ in range(5):
                    ProductFactory(structure="child", parent=parent, categories=[])

        create_parent_child_products()
        self.assertEqual(Product.objects.count(), 64)  # 4 inside the fixtures

        with self.assertNumQueries(19):
            call_command("update_index_products")

        # create 10 extra product with each 5 childs
        create_parent_child_products()

        # The amount of queries should not change.
        with self.assertNumQueries(19):
            call_command("update_index_products")
