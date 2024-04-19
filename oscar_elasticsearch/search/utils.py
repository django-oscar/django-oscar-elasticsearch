def chunked(qs, size, startindex=0):
    """
    Divide an interable into chunks of ``size``

    >>> list(chunked("hahahaha", 2))
    ['ha', 'ha', 'ha', 'ha']
    >>> list(chunked([1,2,3,4,5,6,7], 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    while True:
        chunk = qs[startindex : startindex + size]
        chunklen = len(chunk)
        if chunklen:
            yield chunk
        if chunklen < size:
            break
        startindex += size


class LegacyOscarFacetList(list):
    def items(self):
        for item in self:
            yield None, item
