from fastapi import Request


def get_query_filters(request: Request) -> dict:
    """Extract query parameters for filtering assets."""
    filters = {}
    for key, value in request.query_params.items():
        if key not in [
            "page",
            "per_page",
            "sort_by",
            "sort_order",
            "search",
            "warranty_expired",
        ]:
            filters[key] = value
    if "warranty_expired" in request.query_params:
        filters["warranty_expired"] = (
            request.query_params["warranty_expired"].lower() == "true"
        )
    return filters
