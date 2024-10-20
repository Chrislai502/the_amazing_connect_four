from dataclasses import dataclass, field
from typing import List


@dataclass
class Metrics:
    total_levels: int = 4
    points_per_correct: int = 5
    penalty_per_failed_guess: int = 1
    solves: List[bool] = field(default_factory=lambda: [False]*4)
    failed_guesses: int = 0
    solve_order: List[int] = field(default_factory=list)
    points: int = 0
    tokens_used: dict[str, int] = field(default_factory=dict)

    def increment_failed_guesses(self):
        """Increment the count of failed guesses."""
        self.failed_guesses += 1

    def add_solve(self, level: int):
        """Record a successful solve at the given level."""
        if not self.solves[level]:
            self.solves[level] = True
            self.solve_order.append(level)
            self.points += self.points_per_correct

    def add_tokens(self, model_name: str, token_count: int):
        self.tokens_used[model_name] = \
            self.tokens_used.get(model_name, 0) + token_count

    @property
    def solve_rate(self) -> float:
        """Calculate the solve rate as a percentage."""
        return (sum(self.solves) / self.total_levels) * 100

    @property
    def final_points(self) -> float:
        """Adjust the total points based on penalties."""
        f_points = self.points - self.failed_guesses * self.penalty_per_failed_guess
        return max(f_points, 0)  # Ensure points are not negative

    def to_dict(self) -> dict:
        """Convert the metrics data to a dictionary."""
        return {
            'solves': self.solves,
            'failed_guesses': self.failed_guesses,
            'solve_order': self.solve_order,
            'points': self.points,
            'solve_rate': self.solve_rate,
            'tokens_used': self.tokens_used
        }
