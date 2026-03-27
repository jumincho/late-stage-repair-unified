from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import random
import re
from typing import Iterable


MOVE_DELTAS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}

MOVE_ALIASES = {
    "UP": "U",
    "DOWN": "D",
    "LEFT": "L",
    "RIGHT": "R",
    "NORTH": "U",
    "SOUTH": "D",
    "WEST": "L",
    "EAST": "R",
    "U": "U",
    "D": "D",
    "L": "L",
    "R": "R",
}


@dataclass(slots=True)
class GridTask:
    task_id: str
    split: str
    grid_size: int
    start: tuple[int, int]
    goal: tuple[int, int]
    walls: list[tuple[int, int]]
    shortest_plan: list[str]
    shortest_length: int
    obstacle_density: float
    prompt: str
    metadata: dict[str, str | int | float]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["start"] = list(self.start)
        payload["goal"] = list(self.goal)
        payload["walls"] = [list(item) for item in self.walls]
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "GridTask":
        return cls(
            task_id=str(payload["task_id"]),
            split=str(payload["split"]),
            grid_size=int(payload["grid_size"]),
            start=tuple(payload["start"]),
            goal=tuple(payload["goal"]),
            walls=[tuple(item) for item in payload["walls"]],
            shortest_plan=[str(step) for step in payload["shortest_plan"]],
            shortest_length=int(payload["shortest_length"]),
            obstacle_density=float(payload["obstacle_density"]),
            prompt=str(payload["prompt"]),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class LineWorldTask:
    task_id: str
    split: str
    line_length: int
    start: int
    goal: int
    key_pos: int
    door_pos: int
    shortest_plan: list[str]
    shortest_length: int
    prompt: str
    metadata: dict[str, str | int | float]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "LineWorldTask":
        return cls(
            task_id=str(payload["task_id"]),
            split=str(payload["split"]),
            line_length=int(payload["line_length"]),
            start=int(payload["start"]),
            goal=int(payload["goal"]),
            key_pos=int(payload["key_pos"]),
            door_pos=int(payload["door_pos"]),
            shortest_plan=[str(step) for step in payload["shortest_plan"]],
            shortest_length=int(payload["shortest_length"]),
            prompt=str(payload["prompt"]),
            metadata=dict(payload.get("metadata", {})),
        )


PlanningTask = GridTask | LineWorldTask


def shard_entries(entries: list[dict], *, nshards: int = 4) -> list[list[dict]]:
    shards: list[list[dict]] = [[] for _ in range(nshards)]
    for idx, entry in enumerate(entries):
        shards[idx % nshards].append(entry)
    return [shard for shard in shards if shard]


def _random_cell(rng: random.Random, size: int) -> tuple[int, int]:
    return rng.randrange(size), rng.randrange(size)


def _format_grid(size: int, start: tuple[int, int], goal: tuple[int, int], walls: set[tuple[int, int]]) -> str:
    rows: list[str] = ["    " + " ".join(f"{col:>2d}" for col in range(size))]
    for r in range(size):
        cells: list[str] = []
        for c in range(size):
            coord = (r, c)
            if coord == start:
                cells.append("S")
            elif coord == goal:
                cells.append("G")
            elif coord in walls:
                cells.append("#")
            else:
                cells.append(".")
        rows.append(f"{r:>2d}: " + " ".join(f"{cell:>2s}" for cell in cells))
    return "\n".join(rows)


def _neighbors(size: int, coord: tuple[int, int], walls: set[tuple[int, int]]) -> Iterable[tuple[str, tuple[int, int]]]:
    row, col = coord
    for move, (dr, dc) in MOVE_DELTAS.items():
        nxt = (row + dr, col + dc)
        if 0 <= nxt[0] < size and 0 <= nxt[1] < size and nxt not in walls:
            yield move, nxt


def shortest_plan(size: int, start: tuple[int, int], goal: tuple[int, int], walls: set[tuple[int, int]]) -> list[str] | None:
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        coord, path = queue.popleft()
        if coord == goal:
            return path
        for move, nxt in _neighbors(size, coord, walls):
            if nxt in seen:
                continue
            seen.add(nxt)
            queue.append((nxt, path + [move]))
    return None


def _sample_task(
    *,
    rng: random.Random,
    split: str,
    task_index: int,
    size: int,
    density: float,
    min_length: int,
    max_length: int,
) -> GridTask:
    while True:
        start = _random_cell(rng, size)
        goal = _random_cell(rng, size)
        if start == goal:
            continue
        if abs(start[0] - goal[0]) + abs(start[1] - goal[1]) < size // 2:
            continue
        wall_budget = max(1, int(round(size * size * density)))
        blocked: set[tuple[int, int]] = set()
        while len(blocked) < wall_budget:
            cell = _random_cell(rng, size)
            if cell in {start, goal}:
                continue
            blocked.add(cell)
        best = shortest_plan(size, start, goal, blocked)
        if best is None:
            continue
        if not (min_length <= len(best) <= max_length):
            continue
        grid = _format_grid(size, start, goal, blocked)
        prompt = (
            f"Grid size: {size}x{size}\n"
            f"Legend: S=start, G=goal, #=wall, .=open cell\n"
            f"Moves allowed: U,D,L,R\n"
            f"Grid:\n{grid}\n"
            f"Start: {start}\n"
            f"Goal: {goal}\n"
            "Find a valid move sequence from S to G."
        )
        return GridTask(
            task_id=f"gridworld_{split}_{task_index:04d}",
            split=split,
            grid_size=size,
            start=start,
            goal=goal,
            walls=sorted(blocked),
            shortest_plan=best,
            shortest_length=len(best),
            obstacle_density=density,
            prompt=prompt,
            metadata={
                "domain": "gridworld",
                "difficulty": split,
                "size": size,
                "obstacle_density": density,
            },
        )


def generate_grid_tasks(
    *,
    easy_count: int,
    hard_count: int,
    seed: int = 13,
) -> list[GridTask]:
    rng = random.Random(seed)
    tasks: list[GridTask] = []
    for idx in range(easy_count):
        size = 4 if idx % 2 == 0 else 5
        density = 0.08 if idx % 3 else 0.12
        tasks.append(
            _sample_task(
                rng=rng,
                split="easy",
                task_index=idx,
                size=size,
                density=density,
                min_length=3,
                max_length=6,
            )
        )
    for idx in range(hard_count):
        size = 5 if idx % 2 == 0 else 6
        density = 0.14 if idx % 3 else 0.18
        tasks.append(
            _sample_task(
                rng=rng,
                split="hard",
                task_index=idx,
                size=size,
                density=density,
                min_length=6,
                max_length=10,
            )
        )
    return tasks


def _line_layout(
    length: int,
    *,
    current: int,
    goal: int,
    key_pos: int,
    door_pos: int,
    has_key: bool,
) -> str:
    indices = " ".join(f"{idx:>2d}" for idx in range(length))
    cells: list[str] = []
    for idx in range(length):
        if idx == current:
            cells.append("S")
        elif idx == goal:
            cells.append("G")
        elif idx == key_pos and not has_key:
            cells.append("K")
        elif idx == door_pos:
            cells.append("D")
        else:
            cells.append(".")
    return f"    {indices}\n    " + " ".join(f"{cell:>2s}" for cell in cells)


def _line_shortest_plan(start: int, goal: int, key_pos: int, door_pos: int) -> list[str]:
    steps: list[str] = []
    position = start
    has_key = position == key_pos
    if not has_key:
        move = "L" if key_pos < position else "R"
        while position != key_pos:
            steps.append(move)
            position += -1 if move == "L" else 1
        has_key = True
    move = "L" if goal < position else "R"
    while position != goal:
        nxt = position + (-1 if move == "L" else 1)
        if nxt == door_pos and not has_key:
            raise ValueError("Door is not crossable without the key")
        steps.append(move)
        position = nxt
        has_key = has_key or position == key_pos
    return steps


def _line_task_prompt(length: int, start: int, goal: int, key_pos: int, door_pos: int, *, has_key: bool = False) -> str:
    layout = _line_layout(length, current=start, goal=goal, key_pos=key_pos, door_pos=door_pos, has_key=has_key)
    return (
        f"Line length: {length}\n"
        "Positions are integer cells on a 1D line.\n"
        "Moves allowed: L decreases position by 1, R increases position by 1.\n"
        "You must collect the key K before stepping onto the locked door D.\n"
        f"Current position: {start}\n"
        f"Goal position: {goal}\n"
        f"Has key already: {'yes' if has_key else 'no'}\n"
        f"Layout:\n{layout}\n"
        "Find a valid move sequence from the current position to the goal."
    )


def _sample_line_task(*, rng: random.Random, split: str, task_index: int) -> LineWorldTask:
    while True:
        if split == "easy":
            length = rng.choice([7, 8, 9])
            start = rng.randint(0, 1)
            goal = rng.randint(length - 3, length - 1)
            door_pos = rng.randint(max(start + 2, goal - 2), goal - 1)
            key_pos = rng.randint(start + 1, door_pos - 1)
        else:
            length = rng.choice([10, 11, 12, 13])
            start = rng.randint(3, length - 5)
            goal = rng.randint(length - 3, length - 1)
            if goal - start < 3:
                continue
            door_pos = rng.randint(start + 2, goal - 1)
            key_pos = rng.randint(0, start - 1)
        if len({start, goal, key_pos, door_pos}) < 4:
            continue
        try:
            shortest = _line_shortest_plan(start, goal, key_pos, door_pos)
        except ValueError:
            continue
        if split == "easy" and not (3 <= len(shortest) <= 7):
            continue
        if split == "hard" and not (7 <= len(shortest) <= 15):
            continue
        prompt = _line_task_prompt(length, start, goal, key_pos, door_pos, has_key=False)
        return LineWorldTask(
            task_id=f"lineworld_{split}_{task_index:04d}",
            split=split,
            line_length=length,
            start=start,
            goal=goal,
            key_pos=key_pos,
            door_pos=door_pos,
            shortest_plan=shortest,
            shortest_length=len(shortest),
            prompt=prompt,
            metadata={
                "domain": "lineworld",
                "difficulty": split,
                "line_length": length,
                "door_distance": abs(goal - door_pos),
                "detour_length": abs(start - key_pos),
            },
        )


def generate_line_tasks(*, easy_count: int, hard_count: int, seed: int = 13) -> list[LineWorldTask]:
    rng = random.Random(seed)
    tasks: list[LineWorldTask] = []
    for idx in range(easy_count):
        tasks.append(_sample_line_task(rng=rng, split="easy", task_index=idx))
    for idx in range(hard_count):
        tasks.append(_sample_line_task(rng=rng, split="hard", task_index=idx))
    return tasks


def load_task_from_dict(payload: dict) -> PlanningTask:
    domain = str(payload.get("metadata", {}).get("domain", ""))
    if domain == "lineworld" or "line_length" in payload:
        return LineWorldTask.from_dict(payload)
    return GridTask.from_dict(payload)


def render_task_block(task: PlanningTask, *, current_state: tuple[int, int] | tuple[int, bool] | None = None) -> str:
    if isinstance(task, GridTask):
        anchor = tuple(current_state) if current_state is not None else task.start
        grid = _format_grid(task.grid_size, anchor, task.goal, set(task.walls))
        return (
            f"Grid size: {task.grid_size}x{task.grid_size}\n"
            "Coordinates use (row, col) with (0, 0) at the top-left.\n"
            "Move semantics: U=(row-1,col), D=(row+1,col), L=(row,col-1), R=(row,col+1).\n"
            "Legend: S=current start for this task, G=goal, #=wall, .=open cell.\n"
            f"Grid:\n{grid}\n"
            f"Current start: {anchor}\n"
            f"Goal: {task.goal}\n"
            "Find a valid move sequence from S to G."
        )
    if current_state is None:
        position, has_key = task.start, False
    else:
        position, has_key = int(current_state[0]), bool(int(current_state[1]))
    return _line_task_prompt(task.line_length, position, task.goal, task.key_pos, task.door_pos, has_key=has_key)


def normalize_move_token(token: str) -> str | None:
    cleaned = re.sub(r"[^A-Za-z]", "", token).upper()
    if not cleaned:
        return None
    return MOVE_ALIASES.get(cleaned)


def parse_plan_steps(raw_text: str) -> list[str]:
    tokens = re.split(r"[\s,;|>\-]+", raw_text.strip())
    steps: list[str] = []
    for token in tokens:
        normalized = normalize_move_token(token)
        if normalized:
            steps.append(normalized)
    if not steps:
        compact = re.sub(r"[^UDLR]", "", raw_text.upper())
        steps.extend(list(compact))
    return steps


def compose_repaired_plan(valid_prefix_text: str, suffix_text: str) -> str:
    parts = [part.strip() for part in [valid_prefix_text, suffix_text] if str(part).strip() and str(part).strip().lower() != "none"]
    return ",".join(parts)


def _validate_grid_plan(task: GridTask, plan_text: str) -> dict[str, object]:
    steps = parse_plan_steps(plan_text)
    position = task.start
    valid_prefix: list[str] = []
    failure_type = "goal_not_reached"
    first_invalid_step = len(steps) + 1 if steps else 1
    invalid_step = ""
    for index, move in enumerate(steps, start=1):
        if move not in MOVE_DELTAS:
            failure_type = "invalid_token"
            first_invalid_step = index
            invalid_step = move
            break
        dr, dc = MOVE_DELTAS[move]
        nxt = (position[0] + dr, position[1] + dc)
        if not (0 <= nxt[0] < task.grid_size and 0 <= nxt[1] < task.grid_size):
            failure_type = "out_of_bounds"
            first_invalid_step = index
            invalid_step = move
            break
        if nxt in set(task.walls):
            failure_type = "hit_wall"
            first_invalid_step = index
            invalid_step = move
            break
        valid_prefix.append(move)
        position = nxt
        if position == task.goal and index < len(steps):
            failure_type = "continued_after_goal"
            first_invalid_step = index + 1
            invalid_step = steps[index]
            break
    else:
        if position == task.goal:
            failure_type = "success"
            first_invalid_step = len(steps)
        else:
            failure_type = "goal_not_reached"
            first_invalid_step = len(steps) + 1 if steps else 1

    proposed_len = max(1, len(steps))
    prefix_len = len(valid_prefix)
    return {
        "steps": steps,
        "valid_prefix": valid_prefix,
        "valid_prefix_text": ",".join(valid_prefix),
        "valid_prefix_length": prefix_len,
        "prefix_valid": int(prefix_len == max(0, min(prefix_len, len(steps)))),
        "current_state": list(position),
        "failure_type": failure_type,
        "first_invalid_step": int(first_invalid_step),
        "invalid_step": invalid_step,
        "failure_position_ratio": prefix_len / max(1, proposed_len),
        "reaches_goal": int(position == task.goal and failure_type == "success"),
        "success": int(position == task.goal and failure_type == "success"),
        "plan_length": len(steps),
    }


def _validate_line_plan(task: LineWorldTask, plan_text: str) -> dict[str, object]:
    steps = parse_plan_steps(plan_text)
    position = task.start
    has_key = position == task.key_pos
    valid_prefix: list[str] = []
    failure_type = "goal_not_reached"
    first_invalid_step = len(steps) + 1 if steps else 1
    invalid_step = ""
    for index, move in enumerate(steps, start=1):
        if move not in {"L", "R"}:
            failure_type = "invalid_token"
            first_invalid_step = index
            invalid_step = move
            break
        nxt = position + (-1 if move == "L" else 1)
        if not (0 <= nxt < task.line_length):
            failure_type = "out_of_bounds"
            first_invalid_step = index
            invalid_step = move
            break
        if nxt == task.door_pos and not has_key:
            failure_type = "locked_door_without_key"
            first_invalid_step = index
            invalid_step = move
            break
        valid_prefix.append(move)
        position = nxt
        has_key = has_key or position == task.key_pos
        if position == task.goal and index < len(steps):
            failure_type = "continued_after_goal"
            first_invalid_step = index + 1
            invalid_step = steps[index]
            break
    else:
        if position == task.goal:
            failure_type = "success"
            first_invalid_step = len(steps)
        else:
            failure_type = "goal_not_reached"
            first_invalid_step = len(steps) + 1 if steps else 1

    proposed_len = max(1, len(steps))
    prefix_len = len(valid_prefix)
    return {
        "steps": steps,
        "valid_prefix": valid_prefix,
        "valid_prefix_text": ",".join(valid_prefix),
        "valid_prefix_length": prefix_len,
        "prefix_valid": int(prefix_len == max(0, min(prefix_len, len(steps)))),
        "current_state": [position, int(has_key)],
        "failure_type": failure_type,
        "first_invalid_step": int(first_invalid_step),
        "invalid_step": invalid_step,
        "failure_position_ratio": prefix_len / max(1, proposed_len),
        "reaches_goal": int(position == task.goal and failure_type == "success"),
        "success": int(position == task.goal and failure_type == "success"),
        "plan_length": len(steps),
    }


def validate_plan(task: PlanningTask, plan_text: str) -> dict[str, object]:
    if isinstance(task, GridTask):
        return _validate_grid_plan(task, plan_text)
    return _validate_line_plan(task, plan_text)
