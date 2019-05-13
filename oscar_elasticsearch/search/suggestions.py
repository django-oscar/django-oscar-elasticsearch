def select_suggestion(field, suggestions):
    if field in suggestions:
        try:
            return suggestions[field][0]["options"][0].get("text")
        except (IndexError, ValueError):
            pass

    return None
