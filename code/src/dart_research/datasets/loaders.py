from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from datasets import load_dataset

from dart_research.parsing.normalization import normalize_gold_answer
from dart_research.utils.config import load_yaml


@dataclass(slots=True)
class BenchmarkExample:
    dataset: str
    question_id: str
    question: str
    gold_answer: str
    gold_normalized: str
    task_type: str
    options: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _format_arc_options(raw_choices: dict[str, Any]) -> list[dict[str, str]]:
    labels = raw_choices["label"]
    texts = raw_choices["text"]
    return [{"label": label, "text": text} for label, text in zip(labels, texts, strict=True)]


def _strategyqa_answer_to_text(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return "yes" if value == 1 else "no"
    return str(value)


def _load_one_source(source_cfg: dict[str, Any], split_override: str | None):
    split = split_override or source_cfg["split"]
    path = source_cfg["path"]
    name = source_cfg.get("name")
    if name in {None, "null"}:
        return load_dataset(path, split=split)
    return load_dataset(path, name, split=split)


def load_examples(
    config_path: Path,
    dataset_name: str,
    split_override: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[BenchmarkExample]:
    """Load benchmark examples from the first accessible configured HF source."""
    config = load_yaml(config_path)
    dataset_cfg = config["datasets"][dataset_name]
    last_error: Exception | None = None
    records = None
    selected_source = None

    for source in dataset_cfg["hf_candidates"]:
        try:
            records = _load_one_source(source, split_override)
            selected_source = source
            break
        except Exception as error:  # pragma: no cover - network and remote errors vary
            last_error = error

    if records is None:
        raise RuntimeError(f"Unable to load dataset {dataset_name}") from last_error

    examples: list[BenchmarkExample] = []
    task_type = dataset_cfg["task_type"]
    options_field = dataset_cfg.get("options_field")
    id_field = dataset_cfg.get("id_field", "id")

    for index, row in enumerate(records):
        if index < offset:
            continue
        if limit is not None and len(examples) >= limit:
            break

        question_field = dataset_cfg["question_field"]
        if isinstance(question_field, list):
            question = "\n".join(str(row[field]).strip() for field in question_field).strip()
        else:
            question = str(row[question_field]).strip()
        if dataset_name == "strategyqa" and "passage" in row:
            question = f"Passage: {row['passage'].strip()}\nQuestion: {question}"

        raw_answer = row[dataset_cfg["answer_field"]]
        if dataset_name == "strategyqa":
            answer_text = _strategyqa_answer_to_text(raw_answer)
        else:
            answer_text = str(raw_answer)

        options = []
        if options_field:
            if dataset_name == "arc_challenge":
                options = _format_arc_options(row[options_field])

        question_id = str(row.get(id_field, f"{dataset_name}_{index}"))
        metadata = {
            "hf_source": selected_source["path"],
            "hf_name": selected_source.get("name"),
            "split": split_override or selected_source["split"],
        }
        examples.append(
            BenchmarkExample(
                dataset=dataset_name,
                question_id=question_id,
                question=question,
                gold_answer=answer_text,
                gold_normalized=normalize_gold_answer(answer_text, task_type),
                task_type=task_type,
                options=options,
                metadata=metadata,
            )
        )

    return examples
