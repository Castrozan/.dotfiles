import random


class ShuffledSegmentOrder:
    def __init__(self, segment_count, random_source=None):
        self.segment_count = segment_count
        self.random_source = random_source or random
        self.remaining_segment_indices = []
        self.previously_played_segment_index = None

    def next_segment_index(self):
        if not self.remaining_segment_indices:
            self.refill_avoiding_immediate_repeat()
        chosen_segment_index = self.remaining_segment_indices.pop(0)
        self.previously_played_segment_index = chosen_segment_index
        return chosen_segment_index

    def refill_avoiding_immediate_repeat(self):
        if self.segment_count <= 0:
            return
        shuffled_indices = list(range(self.segment_count))
        self.random_source.shuffle(shuffled_indices)
        if (
            self.segment_count > 1
            and shuffled_indices[0] == self.previously_played_segment_index
        ):
            shuffled_indices[0], shuffled_indices[-1] = (
                shuffled_indices[-1],
                shuffled_indices[0],
            )
        self.remaining_segment_indices = shuffled_indices
