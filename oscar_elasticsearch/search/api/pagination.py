import operator

from django.db.models import Case, When
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


class ElasticSearchPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        self.products = kwargs.pop("products")
        super().__init__(*args, **kwargs)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.products, number, self)


def paginate_result(search_results, Model, size):
    idgetter = operator.itemgetter("id")
    product_ids = [idgetter(hit["_source"]) for hit in search_results["hits"]["hits"]]

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)])
    products = Model.objects.filter(pk__in=product_ids).order_by(preserved)

    total_hits = search_results["hits"]["total"]["value"]

    return ElasticSearchPaginator(range(0, total_hits), size, products=products)
