from oscar.core.loading import get_class

from oscar_elasticsearch.search.settings import NUM_SUGGESTIONS

es = get_class("search.backend", "es")


def get_option_results(results):
    for suggestion in results["suggest"]["autocompletion"]:
        for option in suggestion["options"]:
            yield option["text"]


def autocomplete_suggestions(
    index,
    search_string,
    suggest_field_name,
    skip_duplicates=True,
    contexts=None,
    num_suggestions=NUM_SUGGESTIONS,
):
    body = {
        "suggest": {
            "autocompletion": {
                "prefix": search_string,
                "completion": {
                    "field": suggest_field_name,
                    "skip_duplicates": skip_duplicates,
                },
            }
        },
        "_source": False,
    }

    if contexts is not None:
        body["suggest"]["autocompletion"]["completion"]["contexts"] = contexts

    results = es.search(index=index, body=body)

    return list(get_option_results(results))[:num_suggestions]
