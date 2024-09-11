from django.utils.module_loading import import_string
from django.utils.translation import gettext

from . import settings

from purl import URL


def bucket_key(bucket):
    if "key_as_string" in bucket:
        return bucket["key_as_string"]
    else:
        return bucket["key"]


def bucket_to_lookup(buckets):
    return {bucket_key(item): item["doc_count"] for item in buckets}


def strip_pagination(url):
    if url.has_query_param("page"):
        url = url.remove_query_param("page")
    return url.as_string()


def process_facets(request_full_path, form, facets, facet_definitions=None):
    unfiltered_facets, filtered_facets = facets
    selected_multi_facets = form.selected_multi_facets
    if not facet_definitions:
        facet_definitions = []
    processed_facets = {}

    for facet_definition in facet_definitions:
        facet_name = facet_definition["name"]
        selected_facets = selected_multi_facets[facet_name]
        unfiltered_facet = unfiltered_facets["aggregations"].get(facet_name)
        filtered_facet = filtered_facets["aggregations"].get(facet_name, {})
        if unfiltered_facet is None:
            continue

        unfiltered_buckets = unfiltered_facet.get("buckets", [])
        filtered_buckets = filtered_facet.get("buckets", [])
        if len(unfiltered_buckets) >= settings.MIN_NUM_BUCKETS:
            # range facet buckets are always filled so we need to check if the
            # doc_counts are non-zero to know if they are useful.
            if facet_definition.get("type") == "range" and not any(
                (bucket.get("doc_count", 0) > 0 for bucket in unfiltered_buckets)
            ):
                continue

            # filter out empty buckets
            if facet_definition.get("type") == "date_histogram":
                unfiltered_buckets = filter(
                    lambda bucket: bucket["doc_count"] > 0, unfiltered_buckets
                )
                filtered_buckets = filter(
                    lambda bucket: bucket["doc_count"] > 0, filtered_buckets
                )

            facet = Facet(
                facet_definition,
                unfiltered_buckets,
                filtered_buckets,
                request_full_path,
                selected_facets,
            )
            processed_facets[facet_name] = facet

    return processed_facets


class Facet(object):
    def __init__(
        self,
        facet_definition,
        unfiltered_buckets,
        filtered_buckets,
        request_url,
        selected_facets=None,
    ):
        self.facet = facet_definition["name"]
        self.label = facet_definition["label"]
        self.typ = facet_definition["type"]
        self.unfiltered_buckets = unfiltered_buckets
        self.filtered_buckets = filtered_buckets
        self.request_url = request_url
        self.selected_facets = set(selected_facets)
        self.formatter = None
        formatter = (facet_definition.get("formatter") or "").strip()
        if formatter:
            self.formatter = import_string(formatter)

    def name(self):
        return gettext(str(self.label or ""))

    def has_selection(self):
        return bool(self.selected_facets)

    def results(self):
        lookup = bucket_to_lookup(self.filtered_buckets)
        if lookup:
            max_bucket_count = max(lookup.values())
        else:
            max_bucket_count = 0

        for bucket in self.unfiltered_buckets:
            key = bucket_key(bucket)

            if str(key) in self.selected_facets:
                selected = True
            else:
                selected = False

            if self.has_selection() and not selected:
                doc_count = min(  # I like to explain why this is a great formula
                    lookup.get(key, 0) or max_bucket_count, bucket["doc_count"]
                )
            else:
                doc_count = lookup.get(key, 0)

            yield FacetBucketItem(
                self.facet, key, doc_count, self.request_url, selected, self.formatter
            )


class FacetBucketItem(object):
    def __init__(self, facet, key, doc_count, request_url, selected, formatter=None):
        self.facet = facet
        self.key = key
        self.doc_count = doc_count
        self.request_url = URL(request_url)
        self.selected = selected
        self.show_count = True
        self.formatter = formatter

    def name(self):
        return self.key

    def __str__(self):
        if self.formatter is not None:
            return f"{self.formatter(self.key)!s}"
        return f"{self.key!s}"

    def select_url(self):
        url = self.request_url.append_query_param(
            "selected_facets", "%s:%s" % (self.facet, self.key)
        )
        return strip_pagination(url)

    def deselect_url(self):
        url = self.request_url.remove_query_param(
            "selected_facets", "%s:%s" % (self.facet, self.key)
        )
        return strip_pagination(url)
