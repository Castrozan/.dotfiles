import random


class ShuffledSegmentOrder:
    def __init__(self, segment_sequence_identifiers, random_source=None):
        self.random_source = random_source or random
        self.segment_indices_by_choice = []
        choice_index_by_sequence = {}
        for segment_index, sequence_identifier in enumerate(
            segment_sequence_identifiers
        ):
            if sequence_identifier:
                choice_index = choice_index_by_sequence.get(sequence_identifier)
                if choice_index is None:
                    choice_index = len(self.segment_indices_by_choice)
                    choice_index_by_sequence[sequence_identifier] = choice_index
                    self.segment_indices_by_choice.append([])
            else:
                choice_index = len(self.segment_indices_by_choice)
                self.segment_indices_by_choice.append([])
            self.segment_indices_by_choice[choice_index].append(segment_index)
        self.remaining_choice_indices = []
        self.previously_played_choice_index = None

    def next_segment_indices(self):
        if not self.segment_indices_by_choice:
            return []
        if not self.remaining_choice_indices:
            self.refill_avoiding_immediate_repeat()
        chosen_choice_index = self.remaining_choice_indices.pop(0)
        self.previously_played_choice_index = chosen_choice_index
        return list(self.segment_indices_by_choice[chosen_choice_index])

    def refill_avoiding_immediate_repeat(self):
        choice_count = len(self.segment_indices_by_choice)
        if choice_count <= 0:
            return
        shuffled_indices = list(range(choice_count))
        self.random_source.shuffle(shuffled_indices)
        if (
            choice_count > 1
            and shuffled_indices[0] == self.previously_played_choice_index
        ):
            shuffled_indices[0], shuffled_indices[-1] = (
                shuffled_indices[-1],
                shuffled_indices[0],
            )
        self.remaining_choice_indices = shuffled_indices
