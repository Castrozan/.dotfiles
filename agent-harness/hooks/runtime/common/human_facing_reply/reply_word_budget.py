def exceeds_word_budget(word_count, budget):
    return word_count > budget["maximum_words"] + budget["grace_words"]
