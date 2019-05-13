import re
from copy import deepcopy
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.conf import settings

from wagtail.search.backends.elasticsearch6 import (
    Elasticsearch6SearchBackend,
    Elasticsearch6SearchQueryCompiler,
    Elasticsearch6SearchResults,
    Elasticsearch6Mapping,
)
from wagtail.search.query import PlainText
from wagtail.search.backends.base import FilterFieldError

from .utils import get_facet_table, to_float
from .errors import QueryTooLarge

ORDERING_RE = re.compile(r"(?P<sign>[\-\+]?)(?P<order_by>(.*))")
SPIT_THAT_BITCH_RE = re.compile(r"(?P<field_name>[^\.]+)(?:\.(?P<addition>.*))?")
PAGE_SIZE = getattr(settings, "OSCAR_ELASTICSEARCH_QUERY_PAGE_SIZE")


def range_pairs(range_definition):
    last_result = None
    for _range in range_definition:
        if last_result is not None:
            yield {"from": last_result, "to": _range}
        else:
            yield {"to": _range}

        last_result = _range

    yield {"from": last_result}


class SearchMapping(Elasticsearch6Mapping):
    def get_autocomplete_column_name(self, field):
        return self.get_field_column_name(field).replace(
            "_edgengrams", "_auto_complete"
        )

    def get_document(self, obj):
        doc = super().get_document(obj)
        for field in self.model.get_autocomplete_search_fields():
            field_name = self.get_autocomplete_column_name(field)
            doc[field_name] = field.get_value(obj)

        return doc

    def get_mapping(self):
        mapping = super().get_mapping()
        properties = mapping["doc"]["properties"]
        for field in self.model.get_autocomplete_search_fields():
            field_name = self.get_autocomplete_column_name(field)
            field_mapping = {"type": "completion"}
            field_mapping.update(field.kwargs.get("es_extra", {}))
            properties[field_name] = field_mapping

        return mapping


class SearchResults(Elasticsearch6SearchResults):
    def _facet_to_aggregation(self, facet_name):
        "Format aggregation definition for ES"
        facet = self.query_compiler.get_facet(facet_name)
        if facet is None:
            return {}

        facet_type = facet["type"]
        full_column_name = self.query_compiler.get_field_name_for_path(facet_name)

        if facet_type == self.query_compiler.FACET_TYPE_TERM:
            return {"terms": {"field": full_column_name, "order": {"_key": "asc"}}}

        elif facet_type == self.query_compiler.FACET_TYPE_RANGE:
            ranges = range_pairs(facet["ranges"])
            return {"range": {"field": full_column_name, "ranges": list(ranges)}}

    def suggestions(self, field):
        "See if ES can propoase suggestions based of the field name passed"
        if isinstance(self.query_compiler.query, PlainText):
            field_name = self.query_compiler.get_suggestion_field_name(field)
            body = self._get_es_body(for_count=True)
            body["suggest"] = {
                "text": self.query_compiler.query.query_string,
                field: {"term": {"field": field_name}},
            }

            response = self.backend.es.search(
                index=self.backend.get_index_for_model(
                    self.query_compiler.queryset.model
                ).name,
                body=body,
                size=0,
            )
            return response["suggest"]

        return {}

    def facets(self, *field_names):
        "Fetches facets from ES based on the fieldnames passed"
        aggregations = {}
        for field_path in field_names:
            field_match = SPIT_THAT_BITCH_RE.match(field_path)
            if field_match is not None:
                field_name = field_match.group("field_name")

                # Get field
                field = self.query_compiler._get_filterable_field(  # pylint: disable=protected-access
                    field_name
                )
                if field is None:
                    raise FilterFieldError(
                        'Cannot facet search results with field "%(field_name)s". '
                        'Please add index.FilterField("%(field_name)s") to %(model_name)s.search_fields.'
                        % {
                            "field_name": field_name,
                            "model_name": self.query_compiler.queryset.model.__name__,
                        },
                        field_name=field_name,
                    )

                aggregations[field_path] = self._facet_to_aggregation(field_path)

        if aggregations:
            unfiltered_index = {
                "index": self.backend.get_index_for_model(
                    self.query_compiler.queryset.model
                ).name
            }
            unfiltered_body = {
                "query": self.query_compiler.get_unfiltered_query(),
                "size": 0,
            }
            unfiltered_body["aggregations"] = aggregations

            filtered_index = unfiltered_index
            filtered_body = {"query": self.query_compiler.get_query(), "size": 0}
            filtered_body["aggregations"] = aggregations

            multi_request = [
                unfiltered_index,
                unfiltered_body,
                filtered_index,
                filtered_body,
            ]

            # Send to Elasticsearch
            response = self.backend.es.msearch(body=multi_request)
            unfiltered_response, filtered_response = response["responses"]
            return (
                unfiltered_response["aggregations"],
                filtered_response["aggregations"],
            )

        return {}, {}

    def es_filter(self, **filters):
        new = self._clone()
        new.query_compiler = self.query_compiler.clone(es_filters=filters)
        return new

    def es_order_by(self, ordering):
        new = self._clone()
        new.query_compiler = self.query_compiler.clone(es_ordering=ordering)
        return new

    def _get_results_from_hits(self, hits):
        "Much more efficient implementation that currently in wagtail ES6"
        # Get pks from results
        pks = [hit["_id"] for hit in hits]

        # query for all pks into a dict
        results = self.query_compiler.queryset.in_bulk(pks)

        # Yield results in order given by Elasticsearch
        for index, pk_str in enumerate(pks):
            pk = self.query_compiler.queryset.model._meta.pk.to_python(pk_str)

            result = results.get(pk)

            if result is not None:
                if self._score_field:
                    score = hits[index]["_score"]
                    setattr(result, self._score_field, score)

                yield result

    def autocomplete(self, fields):
        body = {
            "suggest": {
                field: {
                    "prefix": self.query_compiler.query.query_string,
                    "completion": {
                        "field": self.query_compiler.get_autocomplete_field_name(field),
                        "skip_duplicates": True,
                    },
                }
                for field in fields
            },
            "_source": False,
        }
        result = self._do_raw_search(body)
        return result["suggest"]

    def _do_raw_search(self, body):
        if self.stop is not None:
            limit = self.stop - self.start
        else:
            limit = None

        if limit is None:
            raise QueryTooLarge(
                "Query without limit will download entire index, aborting"
            )
        elif limit > PAGE_SIZE:
            raise QueryTooLarge(
                "query_page_size is %i, but %i items where requested"
                % (PAGE_SIZE, limit)
            )

        params = {
            "index": self.backend.get_index_for_model(
                self.query_compiler.queryset.model
            ).name,
            "body": body,
            "_source": False,
            "from_": self.start,
            "size": limit or PAGE_SIZE,
        }

        # Send to Elasticsearch
        return self.backend.es.search(**params)

    def _do_search(self):
        "Search without ever allowing scroll"
        body = self._get_es_body()
        results = self._do_raw_search(body)
        hits = results["hits"]["hits"]

        # Get results
        return self._get_results_from_hits(hits)

    def __len__(self):
        return self.count()


class SearchQueryCompiler(Elasticsearch6SearchQueryCompiler):
    FACET_TYPE_TERM = "term"
    FACET_TYPE_RANGE = "range"
    mapping_class = SearchMapping

    def __init__(
        self,
        queryset,
        query,
        es_filters=None,
        es_ordering=None,
        fields=None,
        operator=None,
        order_by_relevance=True,
        partial_match=True,
    ):
        self.es_filters = es_filters or {}
        self.es_ordering = es_ordering or []
        self.facet_table = get_facet_table()

        super().__init__(
            queryset,
            query,
            fields=fields,
            operator=operator,
            order_by_relevance=not bool(es_ordering) and order_by_relevance,
            partial_match=partial_match,
        )

    def clone(self, es_filters=None, es_ordering=None):
        es_filters_new = deepcopy(self.es_filters)
        if es_filters is not None:
            es_filters_new.update(es_filters)

        ordering = es_ordering if es_ordering is not None else self.es_ordering

        return self.__class__(
            self.queryset,
            self.query,
            es_filters=es_filters_new,
            es_ordering=ordering,
            fields=self.fields,
            order_by_relevance=not bool(ordering) and self.order_by_relevance,
            partial_match=self.partial_match,
        )

    def get_facet(self, facet_name):
        return self.facet_table.get(facet_name)

    @cached_property
    def _autocomplete_field_lookup(self):
        return dict(
            (field.get_attname(self.queryset.model), field)
            for field in self.queryset.model.get_autocomplete_search_fields()
        )

    def _get_autocomplete_field(self, field_attname):
        return self._autocomplete_field_lookup.get(field_attname)

    def get_autocomplete_field_name(self, field_attname):
        autocomplete_field = self._get_autocomplete_field(field_attname)
        return self.mapping.get_autocomplete_column_name(autocomplete_field)

    def get_suggestion_field_name(self, field_attname):
        suggestion_field = self._get_autocomplete_field(field_attname)
        return self.mapping.get_field_column_name(suggestion_field)

    @cached_property
    def _filterable_field_lookup(self):
        return dict(
            (field.get_attname(self.queryset.model), field)
            for field in self.queryset.model.get_filterable_search_fields()
        )

    def _get_filterable_field(self, field_attname):
        return self._filterable_field_lookup.get(field_attname)

    def get_field_name_for_path(self, path):
        field_match = SPIT_THAT_BITCH_RE.match(path)
        if field_match is not None:
            field_name = field_match.group("field_name")
            addition = field_match.group("addition")
            field = self._get_filterable_field(field_name)
            column_name = self.mapping.get_field_column_name(field)

            if addition:
                return "%s.%s" % (column_name, addition)

            return column_name

    def get_es_filters(self):
        es_filters = []
        for facet_name, values in self.es_filters.items():
            facet = self.get_facet(facet_name)
            if facet is None:
                continue

            facet_type = facet["type"]

            if facet_type == self.FACET_TYPE_RANGE:

                range_query = []

                for value in values:
                    start_pattern, end_pattern = value.split("-", maxsplit=1)
                    start = to_float(start_pattern)
                    end = to_float(end_pattern)

                    range_restriction = dict()

                    if start:
                        range_restriction["gte"] = start
                    if end:
                        range_restriction["lt"] = end

                    range_query.append(
                        {
                            "range": {
                                self.get_field_name_for_path(
                                    facet_name
                                ): range_restriction
                            }
                        }
                    )
                es_filters.append({"bool": {"should": range_query}})

            elif facet_type == self.FACET_TYPE_TERM:
                if len(values) > 1:
                    es_filters.append(
                        {"terms": {self.get_field_name_for_path(facet_name): values}}
                    )
                else:
                    value = values[0]
                    es_filters.append(
                        {"match": {self.get_field_name_for_path(facet_name): value}}
                    )

        return es_filters

    def get_es_ordering(self):
        result = []
        for ordering in self.es_ordering:

            if isinstance(ordering, str):
                order = ORDERING_RE.match(ordering)
                if order is not None:
                    order_by = order.group("order_by")
                    order_by_filter = self.mapping.get_field_column_name(
                        self._get_filterable_field(order_by)
                    )
                    if order.group("sign") == "-":
                        result.append({order_by_filter: "desc"})
                    else:
                        result.append(order_by_filter)
            elif ordering:
                result.append(ordering)

        return result

    def get_unfiltered_query(self):
        inner_query = self.get_inner_query()
        filters = super().get_filters()

        if len(filters) == 1:
            return {"bool": {"must": inner_query, "filter": filters[0]}}
        elif len(filters) > 1:
            return {"bool": {"must": inner_query, "filter": filters}}
        else:
            return inner_query

    def get_filters(self):
        return self.get_es_filters() + super().get_filters()

    def get_sort(self):
        default_order = super().get_sort()
        if default_order:
            return self.get_es_ordering() + default_order

        return self.get_es_ordering()


class SearchBackend(Elasticsearch6SearchBackend):
    query_compiler_class = SearchQueryCompiler
    results_class = SearchResults
    mapping_class = SearchMapping

    def search_suggestions(self, query, model_or_queryset, fields):
        "Suggest some search queries, based on the query passed"
        if isinstance(model_or_queryset, QuerySet):
            queryset = model_or_queryset
        else:
            queryset = model_or_queryset.objects.all()

        # Search
        query_compiler_class = self.query_compiler_class
        search_query = query_compiler_class(queryset, query)

        # Check the query
        search_query.check()

        num_suggestions = settings.OSCAR_PRODUCTS_PER_PAGE
        result = self.results_class(self, search_query)[0:num_suggestions]
        return result.autocomplete(fields)
