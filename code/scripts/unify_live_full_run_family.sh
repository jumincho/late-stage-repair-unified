#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${1:?usage: unify_live_full_run_family.sh <model-name> <model-tag> <manifest-root> <out-root> [quantization] [dtype] [max-model-len] [trust-remote-code]}"
MODEL_TAG="${2:?usage: unify_live_full_run_family.sh <model-name> <model-tag> <manifest-root> <out-root> [quantization] [dtype] [max-model-len] [trust-remote-code]}"
MANIFEST_ROOT="${3:?usage: unify_live_full_run_family.sh <model-name> <model-tag> <manifest-root> <out-root> [quantization] [dtype] [max-model-len] [trust-remote-code]}"
OUTROOT="${4:?usage: unify_live_full_run_family.sh <model-name> <model-tag> <manifest-root> <out-root> [quantization] [dtype] [max-model-len] [trust-remote-code]}"
QUANTIZATION="${5:-none}"
DTYPE="${6:-float16}"
MAX_MODEL_LEN="${7:-4096}"
TRUST_REMOTE_CODE="${8:-1}"
GPU_SLOT_COUNT="${UNIFY_LIVE_GPU_SLOTS_PER_DEVICE:-1}"

ROOT="${DART_REPO_ROOT:-/workspace/project}"
CACHE_NAMESPACE="unify_live_full_${MODEL_TAG}_v1"
LOGDIR="$OUTROOT/logs"
mkdir -p "$OUTROOT" "$OUTROOT/math_raw" "$OUTROOT/math_replay" "$OUTROOT/format" "$LOGDIR"

if ! [[ "$GPU_SLOT_COUNT" =~ ^[1-9][0-9]*$ ]]; then
  echo "UNIFY_LIVE_GPU_SLOTS_PER_DEVICE must be a positive integer" >&2
  exit 1
fi

discover_manifests() {
  local manifest_stem="$1"
  python - "$MANIFEST_ROOT" "$manifest_stem" <<'PY'
from pathlib import Path
import sys

manifest_root = Path(sys.argv[1]) / "shards"
manifest_stem = sys.argv[2]
for path in sorted(manifest_root.glob(f"{manifest_stem}__shard*.json")):
    print(path)
PY
}

read_manifest_count() {
  local manifest_path="$1"
  python - "$manifest_path" <<'PY'
from pathlib import Path
import json
import sys

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(len(payload.get("entries", [])))
PY
}

math_output_dir_for_manifest() {
  local manifest_path="$1"
  basename "${manifest_path%.json}"
}

format_output_dir_for_manifest() {
  local surface="$1"
  local manifest_path="$2"
  local stem
  stem="$(basename "${manifest_path%.json}")"
  echo "${surface}_${stem##*__}"
}

run_manifest_queue() {
  local phase_tag="$1"
  local build_cmd_fn="$2"
  shift 2
  local pending_manifests=("$@")
  local -a worker_pids=()
  local -a worker_slots=()
  local -a free_slots=()
  local slot
  local gpu
  for ((slot = 1; slot <= GPU_SLOT_COUNT; slot++)); do
    for gpu in 0 1 2 3; do
      free_slots+=("${gpu}:${slot}")
    done
  done
  local failed=0

  while [[ "${#pending_manifests[@]}" -gt 0 || "${#worker_pids[@]}" -gt 0 ]]; do
    while [[ "${#pending_manifests[@]}" -gt 0 && "${#free_slots[@]}" -gt 0 ]]; do
      local manifest_path="${pending_manifests[0]}"
      pending_manifests=("${pending_manifests[@]:1}")
      local gpu_slot="${free_slots[0]}"
      free_slots=("${free_slots[@]:1}")
      local worker_gpu="${gpu_slot%%:*}"
      local worker_slot="${gpu_slot##*:}"
      "$build_cmd_fn" "$manifest_path" "$worker_gpu" "$worker_slot"
      worker_pids+=("$LAST_WORKER_PID")
      worker_slots+=("$gpu_slot")
      echo "[${phase_tag}] launched $(basename "$manifest_path") on GPU ${worker_gpu} slot ${worker_slot} -> ${LAST_WORKER_LOG}"
    done
    if [[ "${#worker_pids[@]}" -eq 0 ]]; then
      continue
    fi
    local next_pids=()
    local next_slots=()
    local idx
    for idx in "${!worker_pids[@]}"; do
      local pid="${worker_pids[$idx]}"
      local gpu_slot="${worker_slots[$idx]}"
      if kill -0 "$pid" >/dev/null 2>&1; then
        next_pids+=("$pid")
        next_slots+=("$gpu_slot")
        continue
      fi
      if ! wait "$pid"; then
        failed=1
      fi
      free_slots+=("$gpu_slot")
    done
    worker_pids=("${next_pids[@]}")
    worker_slots=("${next_slots[@]}")
    if [[ "${#worker_pids[@]}" -gt 0 ]]; then
      sleep 5
    fi
  done

  return "$failed"
}

run_dmon_window() {
  local prefix="$1"
  local early_timeout="$2"
  local mid_sleep="$3"
  local mid_timeout="$4"
  timeout "${early_timeout}" bash -lc "nvidia-smi dmon -s pucm -d 5 -o TD > '$OUTROOT/${prefix}_early.log'" &
  local early_pid=$!
  (
    sleep "${mid_sleep}"
    timeout "${mid_timeout}" bash -lc "nvidia-smi dmon -s pucm -d 5 -o TD > '$OUTROOT/${prefix}_mid.log'"
  ) &
  local mid_pid=$!
  echo "${early_pid} ${mid_pid}"
}

stop_dmon_window() {
  local early_pid="$1"
  local mid_pid="$2"
  kill "$early_pid" "$mid_pid" >/dev/null 2>&1 || true
  wait "$early_pid" "$mid_pid" >/dev/null 2>&1 || true
}

run_math_collect_surface() {
  local manifest_stem="$1"
  local phase_tag="$2"
  local out_dir="$OUTROOT/math_raw"
  mapfile -t manifest_paths < <(discover_manifests "$manifest_stem")
  if [[ "${#manifest_paths[@]}" -eq 0 ]]; then
    echo "no math collect manifests found for ${manifest_stem}" >&2
    exit 1
  fi
  local pending=()
  local manifest_path
  for manifest_path in "${manifest_paths[@]}"; do
    local shard_dir
    shard_dir="$(math_output_dir_for_manifest "$manifest_path")"
    if [[ ! -f "$out_dir/${shard_dir}/completed.txt" ]]; then
      pending+=("$manifest_path")
    fi
  done
  if [[ "${#pending[@]}" -eq 0 ]]; then
    echo "math collect ${manifest_stem} already complete"
    return
  fi
  _build_math_collect_worker() {
    local manifest_path="$1"
    local gpu="$2"
    local slot="$3"
    local shard_dir
    shard_dir="$(math_output_dir_for_manifest "$manifest_path")"
    local worker_log="$LOGDIR/${phase_tag}_${shard_dir}_gpu${gpu}s${slot}.log"
    HF_HUB_DISABLE_XET=1 CUDA_VISIBLE_DEVICES="$gpu" python "$ROOT/scripts/cass_r4_collect.py" \
      --client hf_local \
      --manifest "$manifest_path" \
      --output-dir "$out_dir/${shard_dir}" \
      --model-name "$MODEL_NAME" \
      --disable-prm \
      --local-quantization "$QUANTIZATION" \
      --local-dtype "$DTYPE" \
      --local-device-map cuda:0 \
      --local-max-model-len "$MAX_MODEL_LEN" \
      --cache-namespace "${CACHE_NAMESPACE}_${phase_tag}" \
      $( [[ "$TRUST_REMOTE_CODE" == "1" ]] && echo --local-trust-remote-code ) \
      > "$worker_log" 2>&1 &
    LAST_WORKER_PID="$!"
    LAST_WORKER_LOG="$worker_log"
  }
  read -r dmon_early_pid dmon_mid_pid < <(run_dmon_window "dmon_${phase_tag}" 28800 3600 1200)
  local start_ts
  start_ts="$(date +%s)"
  local failed=0
  if ! run_manifest_queue "$phase_tag" _build_math_collect_worker "${pending[@]}"; then
    failed=1
  fi
  stop_dmon_window "$dmon_early_pid" "$dmon_mid_pid"
  local end_ts
  end_ts="$(date +%s)"
  echo $((end_ts - start_ts)) > "$OUTROOT/${phase_tag}_runtime_s.txt"
  if [[ "$failed" -ne 0 ]]; then
    echo "math collect phase ${phase_tag} failed" >&2
    exit 1
  fi
}

run_math_replay_surface() {
  local manifest_stem="$1"
  local phase_tag="$2"
  local out_dir="$OUTROOT/math_replay"
  local source_dir="$OUTROOT/math_raw"
  mapfile -t manifest_paths < <(discover_manifests "$manifest_stem")
  if [[ "${#manifest_paths[@]}" -eq 0 ]]; then
    echo "no math replay manifests found for ${manifest_stem}" >&2
    exit 1
  fi
  local pending=()
  local manifest_path
  for manifest_path in "${manifest_paths[@]}"; do
    local shard_dir
    shard_dir="$(math_output_dir_for_manifest "$manifest_path")"
    if [[ ! -f "$out_dir/${shard_dir}/completed.txt" ]]; then
      pending+=("$manifest_path")
    fi
  done
  if [[ "${#pending[@]}" -eq 0 ]]; then
    echo "math replay ${manifest_stem} already complete"
    return
  fi
  mapfile -t replay_inputs < <(
    find "$source_dir" -mindepth 1 -maxdepth 1 -type d \
      \( -name 'gsm8k_train_cluster_live_full__shard*' -o -name 'gsm8k_train_generic_live_full__shard*' \) \
      | sort
  )
  if [[ "${#replay_inputs[@]}" -eq 0 ]]; then
    echo "math replay inputs missing under ${source_dir}" >&2
    exit 1
  fi
  _build_math_replay_worker() {
    local manifest_path="$1"
    local gpu="$2"
    local slot="$3"
    local shard_dir
    shard_dir="$(math_output_dir_for_manifest "$manifest_path")"
    local worker_log="$LOGDIR/${phase_tag}_${shard_dir}_gpu${gpu}s${slot}.log"
    HF_HUB_DISABLE_XET=1 CUDA_VISIBLE_DEVICES="$gpu" python "$ROOT/scripts/cass_bd_collect_partial_replay.py" \
      --client hf_local \
      --input-dirs "${replay_inputs[@]}" \
      --manifest "$manifest_path" \
      --output-dir "$out_dir/${shard_dir}" \
      --model-name "$MODEL_NAME" \
      --local-quantization "$QUANTIZATION" \
      --local-dtype "$DTYPE" \
      --local-device-map cuda:0 \
      --local-max-model-len "$MAX_MODEL_LEN" \
      --cache-namespace "${CACHE_NAMESPACE}_${phase_tag}" \
      $( [[ "$TRUST_REMOTE_CODE" == "1" ]] && echo --local-trust-remote-code ) \
      > "$worker_log" 2>&1 &
    LAST_WORKER_PID="$!"
    LAST_WORKER_LOG="$worker_log"
  }
  read -r dmon_early_pid dmon_mid_pid < <(run_dmon_window "dmon_${phase_tag}" 28800 3600 1200)
  local start_ts
  start_ts="$(date +%s)"
  local failed=0
  if ! run_manifest_queue "$phase_tag" _build_math_replay_worker "${pending[@]}"; then
    failed=1
  fi
  stop_dmon_window "$dmon_early_pid" "$dmon_mid_pid"
  local end_ts
  end_ts="$(date +%s)"
  echo $((end_ts - start_ts)) > "$OUTROOT/${phase_tag}_runtime_s.txt"
  if [[ "$failed" -ne 0 ]]; then
    echo "math replay phase ${phase_tag} failed" >&2
    exit 1
  fi
}

run_format_surface() {
  local surface="$1"
  local manifest_stem="$2"
  local phase_tag="$3"
  mapfile -t manifest_paths < <(discover_manifests "$manifest_stem")
  if [[ "${#manifest_paths[@]}" -eq 0 ]]; then
    echo "no format manifests found for ${manifest_stem}" >&2
    exit 1
  fi
  local pending=()
  local manifest_path
  for manifest_path in "${manifest_paths[@]}"; do
    local shard_dir
    shard_dir="$(format_output_dir_for_manifest "$surface" "$manifest_path")"
    if [[ ! -f "$OUTROOT/format/${shard_dir}/completed.txt" ]]; then
      pending+=("$manifest_path")
    fi
  done
  if [[ "${#pending[@]}" -eq 0 ]]; then
    echo "format ${surface} already complete"
    return
  fi
  _build_format_worker() {
    local manifest_path="$1"
    local gpu="$2"
    local slot="$3"
    local shard_dir
    shard_dir="$(format_output_dir_for_manifest "$surface" "$manifest_path")"
    local worker_log="$LOGDIR/${phase_tag}_${shard_dir}_gpu${gpu}s${slot}.log"
    HF_HUB_DISABLE_XET=1 CUDA_VISIBLE_DEVICES="$gpu" python "$ROOT/scripts/last_pack_collect_format.py" \
      --client hf_local \
      --surface "$surface" \
      --manifest "$manifest_path" \
      --output-dir "$OUTROOT/format/${shard_dir}" \
      --model-name "$MODEL_NAME" \
      --ifeval-repo "$ROOT/external/google-research" \
      --ifbench-repo "$ROOT/external/IFBench" \
      --local-quantization "$QUANTIZATION" \
      --local-dtype "$DTYPE" \
      --local-device-map cuda:0 \
      --local-max-model-len "$MAX_MODEL_LEN" \
      --cache-namespace "${CACHE_NAMESPACE}_${phase_tag}" \
      $( [[ "$TRUST_REMOTE_CODE" == "1" ]] && echo --local-trust-remote-code ) \
      > "$worker_log" 2>&1 &
    LAST_WORKER_PID="$!"
    LAST_WORKER_LOG="$worker_log"
  }
  read -r dmon_early_pid dmon_mid_pid < <(run_dmon_window "dmon_${phase_tag}" 21600 1800 1200)
  local start_ts
  start_ts="$(date +%s)"
  local failed=0
  if ! run_manifest_queue "$phase_tag" _build_format_worker "${pending[@]}"; then
    failed=1
  fi
  stop_dmon_window "$dmon_early_pid" "$dmon_mid_pid"
  local end_ts
  end_ts="$(date +%s)"
  echo $((end_ts - start_ts)) > "$OUTROOT/${phase_tag}_runtime_s.txt"
  if [[ "$failed" -ne 0 ]]; then
    echo "format phase ${phase_tag} failed" >&2
    exit 1
  fi
}

if [[ -f "$OUTROOT/runtime_start_s.txt" ]]; then
  START_TS="$(cat "$OUTROOT/runtime_start_s.txt")"
else
  START_TS="$(date +%s)"
  echo "$START_TS" > "$OUTROOT/runtime_start_s.txt"
fi

run_math_collect_surface "gsm8k_train_cluster_live_full" "math_cluster_raw"
run_math_collect_surface "gsm8k_train_generic_live_full" "math_generic_raw"
run_math_replay_surface "gsm8k_train_cluster_live_full" "math_cluster_replay"
run_math_replay_surface "gsm8k_train_generic_live_full" "math_generic_replay"
run_format_surface "ifeval" "ifeval_screened_live_full" "format_ifeval"
run_format_surface "ifbench" "ifbench_live_full" "format_ifbench"

END_TS="$(date +%s)"
echo "$END_TS" > "$OUTROOT/runtime_end_s.txt"
echo $((END_TS - START_TS)) > "$OUTROOT/runtime_s.txt"
