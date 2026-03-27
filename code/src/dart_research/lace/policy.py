from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass(slots=True)
class ActionPolicyConfig:
    action_names: tuple[str, ...]
    success_columns: dict[str, str]
    latency_columns: dict[str, str]
    direct_action: str
    local_actions: tuple[str, ...]
    restart_actions: tuple[str, ...]
    tie_break_order: tuple[str, ...]


@dataclass(slots=True)
class PolicyMetrics:
    success_rate: float
    utility: float
    intervention_rate: float
    false_intervene_rate: float
    missed_intervene_rate: float
    local_precision: float
    local_recall: float
    avg_latency_s: float
    action_rates: dict[str, float]

    def to_row(self, *, scope: str, policy: str, n: int) -> dict[str, Any]:
        row = {
            "scope": scope,
            "policy": policy,
            "n": int(n),
            "success_rate": float(self.success_rate),
            "utility": float(self.utility),
            "intervention_rate": float(self.intervention_rate),
            "false_intervene_rate": float(self.false_intervene_rate),
            "missed_intervene_rate": float(self.missed_intervene_rate),
            "local_precision": float(self.local_precision),
            "local_recall": float(self.local_recall),
            "avg_latency_s": float(self.avg_latency_s),
        }
        for action_name, rate in self.action_rates.items():
            row[f"rate_{action_name.lower()}"] = float(rate)
        return row


@dataclass(slots=True)
class FittedActionPolicy:
    repair_model: Pipeline | None
    action_model: Pipeline | None
    repair_threshold: float
    feature_columns: tuple[str, ...]
    config: ActionPolicyConfig
    repair_label: str
    intervention_label: str

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype="object")
        if self.repair_model is None:
            return pd.Series([self.config.direct_action] * len(frame), index=frame.index, dtype="object")
        working = frame.copy()
        repair_prob = self.repair_model.predict_proba(working[list(self.feature_columns)])[:, 1]
        needs_repair = repair_prob >= self.repair_threshold
        decisions = pd.Series(self.config.direct_action, index=working.index, dtype="object")
        intervention_rows = working.loc[needs_repair]
        if intervention_rows.empty:
            return decisions
        if self.action_model is None:
            fallback = _first_intervention_action(self.config)
            decisions.loc[intervention_rows.index] = fallback
            return decisions
        predicted = self.action_model.predict(intervention_rows[list(self.feature_columns)])
        decisions.loc[intervention_rows.index] = predicted
        return decisions


def _feature_lists(frame: pd.DataFrame, feature_columns: list[str]) -> tuple[list[str], list[str]]:
    numeric_columns = [column for column in feature_columns if pd.api.types.is_numeric_dtype(frame[column])]
    categorical_columns = [column for column in feature_columns if column not in numeric_columns]
    return numeric_columns, categorical_columns


def _build_preprocessor(frame: pd.DataFrame, *, feature_columns: list[str]) -> ColumnTransformer:
    numeric_columns, categorical_columns = _feature_lists(frame, feature_columns)
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric_columns,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            ),
        ]
    )


def _fit_classifier(
    frame: pd.DataFrame,
    *,
    feature_columns: list[str],
    label_column: str,
) -> Pipeline | None:
    labels = frame[label_column].dropna().astype(str)
    if frame.empty or labels.empty or labels.nunique() <= 1:
        return None
    preprocessor = _build_preprocessor(frame, feature_columns=feature_columns)
    model = Pipeline(
        steps=[
            ("pre", preprocessor),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    random_state=13,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    model.fit(frame[feature_columns], frame[label_column].astype(str))
    return model


def _get_latency(row: pd.Series, action_name: str, config: ActionPolicyConfig) -> float:
    column = config.latency_columns.get(action_name)
    if not column:
        return 0.0
    value = row.get(column, 0.0)
    if pd.isna(value):
        return 0.0
    return float(value)


def _success(row: pd.Series, action_name: str, config: ActionPolicyConfig) -> int:
    column = config.success_columns[action_name]
    value = row.get(column, 0)
    if pd.isna(value):
        return 0
    return int(value)


def oracle_action_for_row(row: pd.Series, config: ActionPolicyConfig) -> str:
    successes = {action_name: _success(row, action_name, config) for action_name in config.action_names}
    best_success = max(successes.values()) if successes else 0
    candidates = [action_name for action_name, value in successes.items() if value == best_success]
    if len(candidates) == 1:
        return candidates[0]
    latency_rank = sorted(candidates, key=lambda action_name: _get_latency(row, action_name, config))
    best_latency = _get_latency(row, latency_rank[0], config)
    latency_candidates = [action_name for action_name in latency_rank if _get_latency(row, action_name, config) == best_latency]
    if len(latency_candidates) == 1:
        return latency_candidates[0]
    tie_rank = {name: idx for idx, name in enumerate(config.tie_break_order)}
    return sorted(latency_candidates, key=lambda action_name: tie_rank.get(action_name, 10_000))[0]


def label_oracle_actions(frame: pd.DataFrame, config: ActionPolicyConfig) -> pd.Series:
    return frame.apply(lambda row: oracle_action_for_row(row, config), axis=1)


def _first_intervention_action(config: ActionPolicyConfig) -> str:
    if config.local_actions:
        return config.local_actions[0]
    if config.restart_actions:
        return config.restart_actions[0]
    for action_name in config.action_names:
        if action_name != config.direct_action:
            return action_name
    return config.direct_action


def evaluate_policy(frame: pd.DataFrame, *, decision_col: str, config: ActionPolicyConfig) -> PolicyMetrics:
    if frame.empty:
        return PolicyMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {action_name: 0.0 for action_name in config.action_names})
    working = frame.copy()
    decisions = working[decision_col].astype(str)
    chosen_success = []
    chosen_latency = []
    oracle_local = []
    direct_better_exists = []
    local_chosen = []
    action_rates = {action_name: float((decisions == action_name).mean()) for action_name in config.action_names}
    oracle_actions = label_oracle_actions(working, config)
    for idx, row in working.iterrows():
        action_name = str(decisions.loc[idx])
        chosen_success.append(_success(row, action_name, config))
        chosen_latency.append(_get_latency(row, action_name, config))
        oracle_action = str(oracle_actions.loc[idx])
        oracle_local.append(int(oracle_action in config.local_actions and _success(row, oracle_action, config) > _success(row, config.direct_action, config)))
        direct_better_exists.append(
            int(
                max(_success(row, name, config) for name in config.action_names if name != config.direct_action)
                > _success(row, config.direct_action, config)
            )
        )
        local_chosen.append(int(action_name in config.local_actions))
    chosen_success_series = pd.Series(chosen_success, index=working.index)
    intervention = (decisions != config.direct_action).astype(int)
    direct_success = working[config.success_columns[config.direct_action]].fillna(0).astype(int)
    false_intervene = ((intervention == 1) & (chosen_success_series <= direct_success)).astype(int)
    missed_intervene = ((intervention == 0) & pd.Series(direct_better_exists, index=working.index).astype(int)).astype(int)
    local_chosen_series = pd.Series(local_chosen, index=working.index).astype(int)
    oracle_local_series = pd.Series(oracle_local, index=working.index).astype(int)
    tp = int(((local_chosen_series == 1) & (oracle_local_series == 1)).sum())
    fp = int(((local_chosen_series == 1) & (oracle_local_series == 0)).sum())
    fn = int(((local_chosen_series == 0) & (oracle_local_series == 1)).sum())
    return PolicyMetrics(
        success_rate=float(chosen_success_series.mean()),
        utility=float(chosen_success_series.mean()),
        intervention_rate=float(intervention.mean()),
        false_intervene_rate=float(false_intervene.mean()),
        missed_intervene_rate=float(missed_intervene.mean()),
        local_precision=float(tp / max(1, tp + fp)),
        local_recall=float(tp / max(1, tp + fn)),
        avg_latency_s=float(pd.Series(chosen_latency, index=working.index).mean()),
        action_rates=action_rates,
    )


def fit_three_action_policy(
    train_frame: pd.DataFrame,
    *,
    feature_columns: list[str],
    config: ActionPolicyConfig,
) -> FittedActionPolicy:
    if train_frame.empty:
        return FittedActionPolicy(
            repair_model=None,
            action_model=None,
            repair_threshold=1.0,
            feature_columns=tuple(feature_columns),
            config=config,
            repair_label="repair_better_than_direct",
            intervention_label="oracle_intervention_action",
        )
    working = train_frame.copy()
    intervention_actions = [action_name for action_name in config.action_names if action_name != config.direct_action]
    working["oracle_action"] = label_oracle_actions(working, config)
    working["repair_better_than_direct"] = working.apply(
        lambda row: int(
            max(_success(row, action_name, config) for action_name in intervention_actions)
            > _success(row, config.direct_action, config)
        ),
        axis=1,
    )
    repair_model = _fit_classifier(
        working,
        feature_columns=feature_columns,
        label_column="repair_better_than_direct",
    )
    working["oracle_intervention_action"] = working.apply(
        lambda row: (
            oracle_action_for_row(row, config)
            if oracle_action_for_row(row, config) != config.direct_action
            else _first_intervention_action(config)
        ),
        axis=1,
    )
    action_train = working[working["repair_better_than_direct"] == 1].copy()
    action_model = _fit_classifier(
        action_train,
        feature_columns=feature_columns,
        label_column="oracle_intervention_action",
    )
    if repair_model is None:
        return FittedActionPolicy(
            repair_model=None,
            action_model=action_model,
            repair_threshold=1.0,
            feature_columns=tuple(feature_columns),
            config=config,
            repair_label="repair_better_than_direct",
            intervention_label="oracle_intervention_action",
        )
    repair_prob = repair_model.predict_proba(working[feature_columns])[:, 1]
    best_threshold = 0.5
    best_metrics = PolicyMetrics(0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1e9, {})
    action_predictions = None
    if action_model is not None:
        action_predictions = pd.Series(action_model.predict(working[feature_columns]), index=working.index, dtype="object")
    else:
        action_predictions = pd.Series(_first_intervention_action(config), index=working.index, dtype="object")
    for threshold_int in range(1, 40):
        threshold = threshold_int / 40
        working["decision"] = config.direct_action
        intervene_index = working.index[repair_prob >= threshold]
        if len(intervene_index):
            working.loc[intervene_index, "decision"] = action_predictions.loc[intervene_index]
        metrics = evaluate_policy(working, decision_col="decision", config=config)
        if (
            metrics.utility > best_metrics.utility
            or (metrics.utility == best_metrics.utility and metrics.intervention_rate < best_metrics.intervention_rate)
            or (
                metrics.utility == best_metrics.utility
                and metrics.intervention_rate == best_metrics.intervention_rate
                and metrics.avg_latency_s < best_metrics.avg_latency_s
            )
        ):
            best_threshold = threshold
            best_metrics = metrics
    return FittedActionPolicy(
        repair_model=repair_model,
        action_model=action_model,
        repair_threshold=best_threshold,
        feature_columns=tuple(feature_columns),
        config=config,
        repair_label="repair_better_than_direct",
        intervention_label="oracle_intervention_action",
    )


def stable_hash_bucket(value: str) -> float:
    digest = hashlib.md5(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF
