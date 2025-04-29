import doctest
from unittest.mock import patch

from time import sleep
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    ProductFactory,
    OrderFactory,
    OrderLineFactory,
)

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

    def test_child_upc_search_suggests_parent(self):
        url = reverse("search:search")
        # searching for child upc
        response = self.client.get("%s?q=kq8000" % url)
        self.assertEqual(response.context["paginator"].count, 1)
        self.assertEqual(response.context["paginator"].instances[0].upc, "jk4000")
        # searching for child title
        response = self.client.get("%s?q=forty" % url)
        self.assertEqual(response.context["paginator"].count, 1)
        self.assertEqual(response.context["paginator"].instances[0].upc, "jk4000")

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

        self.assertEqual(results.count(), 6)
        self.assertEqual(total_hits, 6)

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
        self.assertEqual(results.count(), 6)
        self.assertEqual(total_hits, 6)

    @patch("oscar_elasticsearch.search.settings.INDEXING_CHUNK_SIZE", 2)
    def test_update_index_products_multiple_chunks(self):
        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 0)
        self.assertEqual(total_hits, 0)

        call_command("update_index_products")
        sleep(3)

        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 6)
        self.assertEqual(total_hits, 6)

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
        self.assertEqual(Product.objects.count(), 66)  # 6 inside the fixtures

        with self.assertNumQueries(25):
            call_command("update_index_products")

        # create 10 extra product with each 5 childs
        create_parent_child_products()

        # The amount of queries should not change.
        with self.assertNumQueries(25):
            call_command("update_index_products")

    def test_popularity_based_on_order_lines(self):
        products = []
        for i in range(5):
            product = ProductFactory(
                title=f"VERY UNIQUE TITLE - {i + 1}", categories=[]
            )
            products.append(product)

        call_command("update_index_products")

        results, total_hits = ProductElasticsearchIndex().search(
            query_string="VERY UNIQUE TITLE", raw_results=True
        )
        self.assertEqual(total_hits, 5)
        for hit in results["hits"]["hits"]:
            self.assertEqual(
                hit["_source"]["popularity"],
                None,
                "no orders place yet, so popularity should be None",
            )

        order = OrderFactory()
        for i, product in enumerate(products):
            quantity = int(product.title.split("-")[-1].strip())
            for _ in range(quantity):
                OrderLineFactory(order=order, product=product)

        call_command("update_index_products")

        results, total_hits = ProductElasticsearchIndex().search(
            query_string="VERY UNIQUE TITLE", raw_results=True
        )
        self.assertEqual(total_hits, 5)
        for hit in results["hits"]["hits"]:
            title = hit["_source"]["title"]
            quantity = int(title.split("-")[-1].strip())
            self.assertEqual(
                hit["_source"]["popularity"],
                quantity,
            )

    def test_exception_does_not_delete_index(self):
        call_command("update_index_products")
        sleep(3)

        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 6)
        self.assertEqual(total_hits, 6)

        with self.assertRaises(Exception):
            with ProductElasticsearchIndex().reindex() as index:
                # Trigger an error by not passing products
                index.reindex_objects(Category.objects.all())
                sleep(3)

        # It should still have the same amount of products.
        results, total_hits = self.product_index.search()
        self.assertEqual(results.count(), 6)
        self.assertEqual(total_hits, 6)


class TestBrowsableItems(TestCase):

    def test_child_products_hidden_in_category_view(self):
        for _ in range(2):
            parent = ProductFactory(structure="parent", stockrecords=[])
            for _ in range(5):
                ProductFactory(structure="child", parent=parent, categories=[])

        call_command("update_index_products")
        sleep(3)

        url = reverse("catalogue:index")
        response = self.client.get(url)
        products = response.context_data["page_obj"].object_list

        self.assertEqual(len(products), 2)
        self.assertFalse(any([product.structure == "child" for product in products]))
