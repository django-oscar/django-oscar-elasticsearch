from django.core.paginator import Paginator


class ElasticSearchPaginator(Paginator):
    def __init__(self, instances, *args, **kwargs):
        self.instances = instances
        super().__init__(*args, **kwargs)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.instances, number, self)


def paginate_result(instances, total_hits, size):
    return ElasticSearchPaginator(instances, range(0, total_hits), size)
