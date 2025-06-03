import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, period: float = 1.0):
        self.period = period
        self.last_call = defaultdict(lambda: 0.0)

    def check(self, user_id: int) -> bool:
        now = time.time()
        if now - self.last_call[user_id] < self.period:
            return False
        self.last_call[user_id] = now
        return True
