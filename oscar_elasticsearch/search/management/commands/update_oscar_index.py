# pylint: disable=unused-import
from extendedsearch.commands import WagtailUpdateIndexCommand

DEFAULT_CHUNK_SIZE = 100


class Command(WagtailUpdateIndexCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--backend",
            action="store",
            dest="backend_name",
            default=None,
            help="Specify a backend to update",
        )
        parser.add_argument(
            "--schema-only",
            action="store_true",
            dest="schema_only",
            default=False,
            help="Prevents loading any data into the index",
        )
        parser.add_argument(
            "--chunk_size",
            dest="chunk_size",
            type=int,
            default=DEFAULT_CHUNK_SIZE,
            help="Set number of records to be fetched at once for inserting into the index",
        )
