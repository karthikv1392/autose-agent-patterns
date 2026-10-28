def page_count(total_items, per_page):
    return max(1, -(-total_items // per_page))


def paginate(items, page, per_page):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]


def page_window(current, total_pages, size=5):
    if total_pages <= size:
        return list(range(1, total_pages + 1))
    start = max(1, min(current - size // 2, total_pages - size + 1))
    return list(range(start, start + size))
