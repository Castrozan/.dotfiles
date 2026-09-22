from reply_format_configuration import exceeds_word_budget


class ReplyListItem:
    def __init__(self, source_range, source_lines, prose_line_indices):
        line_indices = set(range(*source_range)) & prose_line_indices
        self.word_count = sum(
            len(source_lines[index].split()) for index in line_indices
        )


class ReplyList:
    def __init__(self, source_range, prose_line_indices):
        self.line_indices = set(range(*source_range)) & prose_line_indices
        self.line_count = len(self.line_indices)
        self.items = []

    def is_exempt(self, configuration):
        return len(self.items) <= configuration.lists["maximum_exempt_items"] and all(
            not exceeds_word_budget(item.word_count, configuration.lists["item"])
            for item in self.items
        )


def extract_reply_lists(tokens, source_lines, prose_line_indices):
    lists = []
    active_lists = []
    for token in tokens:
        if token.type in ("bullet_list_open", "ordered_list_open"):
            block = ReplyList(token.map, prose_line_indices)
            lists.append(block)
            active_lists.append(block)
        elif token.type in ("bullet_list_close", "ordered_list_close"):
            active_lists.pop()
        elif token.type == "list_item_open":
            active_lists[-1].items.append(
                ReplyListItem(token.map, source_lines, prose_line_indices)
            )
    return lists
