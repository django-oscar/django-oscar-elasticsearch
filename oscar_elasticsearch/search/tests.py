import doctest

import oscar_elasticsearch.search.format
import oscar_elasticsearch.search.utils


def load_tests(loader, tests, ignore):  # pylint: disable=W0613
    tests.addTests(doctest.DocTestSuite(oscar_elasticsearch.search.format))
    tests.addTests(doctest.DocTestSuite(oscar_elasticsearch.search.utils))
    return tests
