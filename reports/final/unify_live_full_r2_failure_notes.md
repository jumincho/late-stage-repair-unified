# UNIFY-LIVE-FULL-R2 Failure Notes

- `Qwen-7B` paper-safe: `1`.
- `Mistral-7B` paper-safe: `1`.
- The resumed Mistral parent runner left restart metadata but no duplicate rows, no incomplete completed-shard artifacts, and no raw/replay ID mismatch.
- `Qwen-14B` is now paper-safe on the completed R2 run root and can be used as a bounded scale-compression check.
- `IFBench` remains the harder boundary surface and should still be read as a stress test rather than a parity target.