from collections import deque
from typing import Deque, List, Tuple

import numpy as np


Transition = Tuple[np.ndarray, int, float, np.ndarray, bool]


class ReplayBuffer:
    def __init__(self, capacity: int):
        self._data: Deque[Transition] = deque(maxlen=capacity)

    def add(self, transition: Transition) -> None:
        self._data.append(transition)

    def sample(self, batch_size: int) -> List[Transition]:
        idxs = np.random.choice(len(self._data), size=batch_size, replace=False)
        return [self._data[i] for i in idxs]

    def __len__(self) -> int:
        return len(self._data)
