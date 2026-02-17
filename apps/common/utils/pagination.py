ELLIPSIS = '…'


def build_olx_page_items(paginator, page_obj):
    """Return OLX-like page items for a paginator/page pair.

    Output contains ints and the ellipsis character.
    """
    total_pages = max(1, int(getattr(paginator, 'num_pages', 1) or 1))
    current_page = int(getattr(page_obj, 'number', 1) or 1)

    if total_pages <= 1:
        return [1]

    if total_pages <= 5:
        return list(range(1, total_pages + 1))

    pages = {1, total_pages, current_page - 1, current_page, current_page + 1}
    normalized = sorted(page for page in pages if 1 <= page <= total_pages)

    items = []
    prev = None
    for page in normalized:
        if prev is not None and page - prev > 1:
            items.append(ELLIPSIS)
        items.append(page)
        prev = page

    return items
