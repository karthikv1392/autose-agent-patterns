"""Pagination helpers. Pages are 1-based."""


def page_count(total_items, per_page):
    """Number of pages needed to show total_items. At least 1, even when empty."""
    return total_items // per_page


def paginate(items, page, per_page):
    """Return the items on the given page.

    Pages beyond the last one return []. Raises ValueError if page < 1 or per_page < 1.
    """
    start = page * per_page
    end = start + per_page
    return items[start:end]


def page_window(current, total_pages, size=5):
    """Page numbers to show in a pager widget.

    Up to `size` consecutive page numbers centred on `current`. Never lists a page
    below 1 or above total_pages; near either edge the window slides so it still
    shows `size` pages whenever total_pages allows. If total_pages <= size, show all pages.
    """
    start = max(1, current - size // 2)
    end = start + size
    return list(range(start, end))
