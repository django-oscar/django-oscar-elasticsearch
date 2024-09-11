# pylint: disable=W0102
from oscar.core.loading import get_class
from django.conf import settings
from oscar_elasticsearch.exceptions import ElasticSearchQueryException
from oscar_elasticsearch.search import settings as es_settings
from oscar_elasticsearch.search.api.base import BaseModelIndex
from oscar_elasticsearch.search.utils import search_result_to_queryset

paginate_result = get_class("search.api.pagination", "paginate_result")
es = get_class("search.backend", "es")


def get_search_query(
    search_fields=[], query_string=None, search_type=None, search_operator=None
):
    if query_string:
        return [
            {
                "multi_match": {
                    "query": query_string,
                    "type": search_type,
                    "operator": search_operator,
                    "fields": search_fields,
                }
            }
        ]

    else:
        return {"match_all": {}}


def get_search_body(
    from_=None,
    size=None,
    search_fields=[],
    query_string=None,
    filters=None,
    sort_by=None,
    suggestion_field_name=None,
    search_type=None,
    search_operator=None,
    aggs=None,
    explain=True,
    field_value_factors=None,
):
    if field_value_factors is None:
        field_value_factors = []

    body = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": get_search_query(
                            search_fields, query_string, search_type, search_operator
                        ),
                        "filter": filters,
                    }
                },
                "functions": field_value_factors,
            }
        }
    }

    if explain:
        body["explain"] = settings.DEBUG

    if from_:
        body["from"] = from_

    if size:
        body["size"] = size

    if sort_by:
        body["sort"] = sort_by

    if aggs:
        body["aggs"] = aggs

    if suggestion_field_name and query_string:
        body["suggest"] = {
            suggestion_field_name: {
                "prefix": query_string,
                "term": {"field": suggestion_field_name},
            }
        }

    return body


def do_count(
    index,
    query_string=None,
    search_fields=[],
    filters=None,
    search_type=None,
    search_operator=None,
):
    body = get_search_body(
        query_string=query_string,
        search_fields=search_fields,
        filters=filters,
        search_type=search_type,
        search_operator=search_operator,
        explain=False,
    )

    result = es.count(index=index, body=body)

    return result.get("count", 0)


def get_elasticsearch_aggs(aggs_definitions):
    aggs = {}

    for facet_definition in aggs_definitions:
        name = facet_definition["name"]
        facet_type = facet_definition["type"]
        if facet_type == "term":
            terms = {"terms": {"field": name, "size": es_settings.FACET_BUCKET_SIZE}}

            if "order" in facet_definition:
                terms["terms"]["order"] = {"_key": facet_definition.get("order", "asc")}

            aggs[name] = terms
        elif facet_type == "range":
            ranges_definition = facet_definition["ranges"]
            if ranges_definition:
                ranges = [
                    (
                        {"to": ranges_definition[i]}
                        if i == 0
                        else {
                            "from": ranges_definition[i - 1],
                            "to": ranges_definition[i],
                        }
                    )
                    for i in range(len(ranges_definition))
                ]

                ranges.append({"from": ranges_definition[-1]})

                aggs[name] = {
                    "range": {
                        "field": name,
                        "ranges": ranges,
                    }
                }

        elif facet_type == "date_histogram":
            date_histogram = {"date_histogram": {"field": name}}

            if "order" in facet_definition:
                date_histogram["date_histogram"]["order"] = {
                    "_key": facet_definition.get("order", "asc")
                }

            if "date_format" in facet_definition:
                date_histogram["date_histogram"]["format"] = facet_definition.get(
                    "date_format"
                )

            if "calendar_interval" in facet_definition:
                date_histogram["date_histogram"]["calendar_interval"] = (
                    facet_definition.get("calendar_interval")
                )

            aggs[name] = date_histogram

    return aggs


def search(
    index,
    from_,
    size,
    search_fields=[],
    query_string=None,
    filters=None,
    sort_by=None,
    suggestion_field_name=None,
    search_type=es_settings.SEARCH_QUERY_TYPE,
    search_operator=es_settings.SEARCH_QUERY_OPERATOR,
    field_value_factors=None,
):
    body = get_search_body(
        from_,
        size,
        search_fields=search_fields,
        query_string=query_string,
        filters=filters,
        sort_by=sort_by,
        suggestion_field_name=suggestion_field_name,
        search_type=search_type,
        search_operator=search_operator,
        field_value_factors=field_value_factors,
    )
    return es.search(index=index, body=body)


def facet_search(
    index,
    from_,
    size,
    search_fields=[],
    query_string=None,
    default_filters=None,
    facet_filters=None,
    sort_by=None,
    suggestion_field_name=None,
    search_type=es_settings.SEARCH_QUERY_TYPE,
    search_operator=es_settings.SEARCH_QUERY_OPERATOR,
    aggs_definitions=None,
    field_value_factors=None,
):

    aggs = get_elasticsearch_aggs(aggs_definitions) if aggs_definitions else {}
    index_body = {"index": index}

    result_body = get_search_body(
        from_,
        size,
        search_fields=search_fields,
        query_string=query_string,
        filters=default_filters + facet_filters,
        sort_by=sort_by,
        suggestion_field_name=suggestion_field_name,
        search_type=search_type,
        search_operator=search_operator,
        aggs=aggs,
        field_value_factors=field_value_factors,
    )

    unfiltered_body = get_search_body(
        0,
        0,
        search_fields=search_fields,
        query_string=query_string,
        filters=default_filters,
        sort_by=sort_by,
        suggestion_field_name=suggestion_field_name,
        search_type=search_type,
        search_operator=search_operator,
        aggs=aggs,
        field_value_factors=field_value_factors,
    )

    multi_body = [
        index_body,
        result_body,
        index_body,
        unfiltered_body,
    ]
    search_results, unfiltered_result = es.msearch(body=multi_body)["responses"]

    search_result_status = search_results["status"]
    unfiltered_result_status = unfiltered_result["status"]

    if search_result_status > 200:
        raise ElasticSearchQueryException(
            "Something went wrong during elasticsearch query", search_results
        )
    elif unfiltered_result_status > 200:
        raise ElasticSearchQueryException(
            "Something went wrong during elasticsearch query", unfiltered_result_status
        )

    return (
        search_results,
        unfiltered_result,
    )


class BaseElasticSearchApi(BaseModelIndex):
    Model = None
    SEARCH_FIELDS = []
    SUGGESTION_FIELD_NAME = None

    def get_search_fields(self, search_fields):
        if search_fields:
            return search_fields

        return self.SEARCH_FIELDS

    def get_filters(self, filters):
        if filters is not None:
            return filters

        return []

    def format_filters(self, filters):
        return [{"match": {key: value}} for key, value in filters.items()]

    def format_order_by(self, order_by):
        orderings = []
        for ordering in filter(None, order_by):
            if ordering.startswith("-"):
                orderings.append({ordering[1:]: "desc"})
            else:
                orderings.append(ordering)
        return orderings

    def get_suggestion_field_name(self, suggestion_field_name):
        if suggestion_field_name is not None:
            return suggestion_field_name

        return self.SUGGESTION_FIELD_NAME

    def make_queryset(self, search_result):
        return search_result_to_queryset(search_result, self.get_model())

    def search(
        self,
        query_string=None,
        filters=None,
        from_=0,
        to=es_settings.DEFAULT_ITEMS_PER_PAGE,
        search_fields=[],
        sort_by=None,
        suggestion_field_name=None,
        search_type=es_settings.SEARCH_QUERY_TYPE,
        search_operator=es_settings.SEARCH_QUERY_OPERATOR,
        field_value_factors=None,
    ):
        search_results = search(
            self.get_index_name(),
            from_,
            to,
            search_fields=self.get_search_fields(search_fields),
            query_string=query_string,
            filters=self.get_filters(filters),
            sort_by=sort_by,
            suggestion_field_name=self.get_suggestion_field_name(suggestion_field_name),
            search_type=search_type,
            search_operator=search_operator,
            field_value_factors=field_value_factors,
        )

        total_hits = search_results["hits"]["total"]["value"]
        total_relation = search_results["hits"]["total"].get("relation", "")

        if total_relation == "gte":
            # The total hits is higher than max_result_window, we want to do another query to get the correct total
            total_hits = do_count(
                self.get_index_name(),
                query_string=query_string,
                search_fields=search_fields,
                filters=filters,
                search_type=search_type,
                search_operator=search_operator,
            )

        return self.make_queryset(search_results), total_hits

    def facet_search(
        self,
        from_=0,
        to=es_settings.DEFAULT_ITEMS_PER_PAGE,
        query_string=None,
        search_fields=[],
        filters=None,
        facet_filters=None,
        sort_by=None,
        suggestion_field_name=None,
        search_type=es_settings.SEARCH_QUERY_TYPE,
        search_operator=es_settings.SEARCH_QUERY_OPERATOR,
        aggs_definitions=None,
        field_value_factors=None,
    ):
        search_results, unfiltered_result = facet_search(
            self.get_index_name(),
            from_,
            to,
            search_fields=self.get_search_fields(search_fields),
            query_string=query_string,
            default_filters=self.get_filters(filters),
            facet_filters=facet_filters,
            sort_by=sort_by,
            suggestion_field_name=self.get_suggestion_field_name(suggestion_field_name),
            search_type=search_type,
            search_operator=search_operator,
            aggs_definitions=aggs_definitions,
            field_value_factors=field_value_factors,
        )

        return (
            self.make_queryset(search_results),
            search_results,
            unfiltered_result,
        )

    def paginated_search(
        self,
        query_string=None,
        filters=None,
        from_=0,
        to=es_settings.DEFAULT_ITEMS_PER_PAGE,
        search_fields=[],
        sort_by=None,
        suggestion_field_name=None,
        search_type=es_settings.SEARCH_QUERY_TYPE,
        search_operator=es_settings.SEARCH_QUERY_OPERATOR,
        field_value_factors=None,
    ):
        instances, total_hits = self.search(
            query_string=query_string,
            filters=filters,
            from_=from_,
            to=to,
            search_fields=search_fields,
            sort_by=sort_by,
            suggestion_field_name=suggestion_field_name,
            search_type=search_type,
            search_operator=search_operator,
            field_value_factors=field_value_factors,
        )

        return paginate_result(instances, total_hits, to)

    def paginated_facet_search(
        self,
        from_=0,
        to=es_settings.DEFAULT_ITEMS_PER_PAGE,
        query_string=None,
        search_fields=[],
        filters=None,
        facet_filters=None,
        sort_by=None,
        suggestion_field_name=None,
        search_type=es_settings.SEARCH_QUERY_TYPE,
        search_operator=es_settings.SEARCH_QUERY_OPERATOR,
        aggs_definitions=None,
        field_value_factors=None,
    ):
        instances, search_results, unfiltered_result = self.facet_search(
            from_=from_,
            to=to,
            query_string=query_string,
            search_fields=search_fields,
            filters=filters,
            facet_filters=facet_filters,
            sort_by=sort_by,
            suggestion_field_name=suggestion_field_name,
            search_type=search_type,
            search_operator=search_operator,
            aggs_definitions=aggs_definitions,
            field_value_factors=field_value_factors,
        )

        total_hits = search_results["hits"]["total"]["value"]
        total_relation = search_results["hits"]["total"].get("relation", "")

        if total_relation == "gte":
            # The total hits is higher than max_result_window, we want to do another query to get the correct total
            total_hits = do_count(
                self.get_index_name(),
                query_string=query_string,
                search_fields=search_fields,
                filters=filters + facet_filters,
                search_type=search_type,
                search_operator=search_operator,
            )

        return (
            paginate_result(instances, total_hits, to),
            search_results,
            unfiltered_result,
        )
