def chunked(items: list, size: int):
    if size <= 0:
        raise ValueError("size must be > 0")
    for index in range(0, len(items), size):
        yield items[index : index + size]



