import operator

from django.db.models import Case, When
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


class ElasticSearchPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        self.instances = kwargs.pop("instances")
        super().__init__(*args, **kwargs)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.instances, number, self)


def paginate_result(search_results, Model, size):
    instances = search_result_to_queryset(search_results, Model)

    total_hits = search_results["hits"]["total"]["value"]

    return ElasticSearchPaginator(range(0, total_hits), size, instances=instances)


def search_result_to_queryset(search_results, Model):
    instance_ids = [hit["_source"]["id"] for hit in search_results["hits"]["hits"]]

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(instance_ids)])
    return Model.objects.filter(pk__in=instance_ids).order_by(preserved)
