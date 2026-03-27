from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any

import torch
import torch.nn.functional as F

from dart_research.utils.cache import DiskCache

try:
    from transformers import AutoConfig, AutoModel, AutoTokenizer
except ImportError:  # pragma: no cover - optional dependency guard
    AutoConfig = None
    AutoModel = None
    AutoTokenizer = None


class ProcessRewardModelScorer:
    """Score stage reasoning with a local PRM and cache results on disk."""

    CACHE_VERSION = "vchase_prm_v1"

    def __init__(
        self,
        *,
        cache_dir: Path,
        model_name: str = "Qwen/Qwen2.5-Math-PRM-7B",
        dtype: str = "float16",
        device_map: str = "auto",
        trust_remote_code: bool = True,
        revision: str | None = None,
    ) -> None:
        if AutoModel is None or AutoTokenizer is None or AutoConfig is None:
            raise RuntimeError("transformers is not installed")
        self.cache = DiskCache(cache_dir / "vchase_prm")
        self.model_name = model_name
        self.dtype = getattr(torch, dtype, torch.float16)
        self.device_map = device_map
        self.trust_remote_code = trust_remote_code
        self.revision = revision
        self._loaded: tuple[Any, Any] | None = None

    def _load(self) -> tuple[Any, Any]:
        if self._loaded is not None:
            return self._loaded
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
        config = AutoConfig.from_pretrained(
            self.model_name,
            token=token,
            revision=self.revision,
            trust_remote_code=self.trust_remote_code,
        )
        if getattr(config, "pad_token_id", None) is None:
            config.pad_token_id = getattr(config, "eos_token_id", None) or getattr(config, "bos_token_id", None) or 0
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=token,
            revision=self.revision,
            trust_remote_code=self.trust_remote_code,
        )
        model = AutoModel.from_pretrained(
            self.model_name,
            token=token,
            revision=self.revision,
            trust_remote_code=self.trust_remote_code,
            device_map=self.device_map,
            config=config,
            dtype=self.dtype,
        ).eval()
        self._loaded = (tokenizer, model)
        return self._loaded

    def score_reasoning(self, *, question: str, scratch: str, answer: str) -> dict[str, float]:
        request = {
            "cache_version": self.CACHE_VERSION,
            "model_name": self.model_name,
            "question": question,
            "scratch": scratch,
            "answer": answer,
            "revision": self.revision or "",
            "device_map": self.device_map,
            "dtype": str(self.dtype),
        }
        cached = self.cache.get(request)
        if cached is not None:
            return cached
        tokenizer, model = self._load()
        steps = _split_steps(scratch, answer)
        messages = [
            {"role": "system", "content": "Please reason step by step, and put your final answer within \\boxed{}."},
            {"role": "user", "content": question},
            {"role": "assistant", "content": "<extra_0>".join(steps) + "<extra_0>"},
        ]
        conversation = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        device = next(model.parameters()).device
        input_ids = tokenizer.encode(conversation, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(input_ids=input_ids, use_cache=False)
        logits = outputs[0] if isinstance(outputs, tuple) else outputs.logits
        step_sep_id = tokenizer.encode("<extra_0>", add_special_tokens=False)[0]
        token_masks = input_ids == step_sep_id
        probabilities = F.softmax(logits, dim=-1) * token_masks.unsqueeze(-1)
        non_zero = probabilities[0][probabilities[0] != 0]
        if non_zero.numel() == 0:
            payload = {
                "prm_score_current": 0.5,
                "prm_score_mean": 0.5,
                "prm_score_min": 0.5,
                "prm_step_count": 0,
            }
        else:
            positive_probs = non_zero.view(-1, 2)[:, 1].detach().cpu().tolist()
            payload = {
                "prm_score_current": float(positive_probs[-1]),
                "prm_score_mean": float(sum(positive_probs) / len(positive_probs)),
                "prm_score_min": float(min(positive_probs)),
                "prm_step_count": int(len(positive_probs)),
            }
        self.cache.set(request, payload)
        return payload


def _split_steps(scratch: str, answer: str) -> list[str]:
    text = scratch.strip()
    if not text:
        return [f"The answer is {answer}."]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2:
        steps = lines
    elif "=" in text:
        parts = [part.strip() for part in text.split("=") if part.strip()]
        if len(parts) >= 2:
            steps = [f"{parts[index]} = {parts[index + 1]}" for index in range(len(parts) - 1)]
        else:
            steps = [text]
    else:
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
        steps = sentences or [text]
    final_step = f"Final answer: {answer}."
    if answer not in steps[-1]:
        steps.append(final_step)
    return steps
