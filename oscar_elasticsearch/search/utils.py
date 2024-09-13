from django.db.models import Case, When


def chunked(iterable, size, startindex=0):
    """
    Divide an interable into chunks of ``size``

    >>> list(chunked("hahahaha", 2))
    ['ha', 'ha', 'ha', 'ha']
    >>> list(chunked([1,2,3,4,5,6,7], 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    while True:
        chunk = iterable[startindex : startindex + size]
        chunklen = len(chunk)
        if chunklen:
            yield chunk
        if chunklen < size:
            break
        startindex += size


def search_result_to_queryset(search_results, Model):
    instance_ids = [hit["_source"]["id"] for hit in search_results["hits"]["hits"]]

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(instance_ids)])
    return Model.objects.filter(pk__in=instance_ids).order_by(preserved)
