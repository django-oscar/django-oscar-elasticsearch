from django.dispatch import Signal

user_search = Signal(providing_args=["session_id", "user", "query"])
query_hit = Signal(providing_args=["querystring"])
