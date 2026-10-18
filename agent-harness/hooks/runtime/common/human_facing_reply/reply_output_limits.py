def exceeds_word_budget(word_count, budget):
    return word_count > budget["maximum_words"] + budget["grace_words"]


def list_block_length_violation(reply):
    maximum_items = reply.configuration.lists["maximum_items"]
    for block in reply.list_blocks:
        if block.item_count > maximum_items:
            return reply.configuration.violation(
                "list_block_length",
                item_count=block.item_count,
                maximum_items=maximum_items,
            )
    return None


def list_line_word_violation(reply):
    budget = reply.configuration.lists["item"]
    for block in reply.list_blocks:
        for item in block.items:
            if exceeds_word_budget(item.word_count, budget):
                return reply.configuration.violation(
                    "list_line_words", word_count=item.word_count, **budget
                )
    return None


def table_block_length_violation(reply):
    maximum_rows = reply.configuration.tables["maximum_rows"]
    for table_number, column in enumerate(reply.table_first_columns, start=1):
        row_count = len(column) - 1
        if row_count > maximum_rows:
            return reply.configuration.violation(
                "table_block_length",
                table_number=table_number,
                row_count=row_count,
                maximum_rows=maximum_rows,
            )
    return None
