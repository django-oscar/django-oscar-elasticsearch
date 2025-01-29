class TermLookupRegistry:
    _lookups = []

    def register(self, cls):
        self._lookups.append(cls)

    @property
    def lookups(self):
        return self._lookups


termlookup_registry = TermLookupRegistry()
