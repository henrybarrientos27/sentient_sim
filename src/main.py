# =====================
# File: main.py
# =====================
# Robust simulation runner with:
# - full use of your existing world/agents logic
# - bounded history.json (prevents slowdown)
# - periodic snapshots
# - autosave/resume of world state via state.py (world_to_dict/world_from_dict)
# - optional UPS (Universal Problem Seeds) hook, gated by a single flag
# - optional sentience metrics & tests if sentience_metrics.py / sentience_test.py exist
# - zero constraints on what agents can build/do (world governs behavior)

import json
import sys
import time
from pathlib import Path

# Optional sentience tools (auto-skip if not present)
_SENTIENCE_METRICS_FN = None
_SENTIENCE_TEST_FN = None
try:
    import sentience_metrics as _sm
    if hasattr(_sm, "compute_metrics"):
        _SENTIENCE_METRICS_FN = _sm.compute_metrics
except Exception:
    pass
try:
    import sentience_test as _st
    if hasattr(_st, "run_sentience_test"):
        _SENTIENCE_TEST_FN = _st.run_sentience_test
except Exception:
    pass

SENTIENCE_INTERVAL = 25            # how often to evaluate
SENTIENCE_ALERT_THRESHOLD = 0.80   # tune this
SENTIENCE_STREAM = Path(__file__).parent / "sentience_stream.jsonl"

# --- Kerr spec / referee hook ---
from ups.referee import score_kerr_spec  # make sure the function is available as shown earlier
SPEC_PATH = None
SPEC_EVAL_EVERY = 50  # evaluate/score every N ticks (adjust as you like)

# ---------------- Config ----------------
ROOT = Path(__file__).parent.resolve()
HISTORY_FILE = ROOT / "history.json"
SNAPSHOT_DIR = ROOT / "snapshots"
SAVE_FILE = ROOT / "save_state.json"

SNAPSHOT_DIR.mkdir(exist_ok=True)

MAX_HISTORY_ENTRIES = 5000        # keep history small & fast
SNAPSHOT_INTERVAL = 250           # ticks between snapshots & autosaves
SLEEP_PER_TICK = 0.05             # pacing; set 0 for max speed
RUN_TICKS = 0                     # 0 = run forever

# Gate UPS until you WANT to seed problems (keep False until agents are sentient)
ENABLE_UPS = False
# Auto-run your sentience tools if present (no import = silently skipped)
SENTIENCE_INTERVAL = 1
SENTIENCE_ALERT_THRESHOLD = 0.80   # print console alert when score crosses this

# ------------- Optional UPS -------------
try:
    from ups.runner import tick_ups  # optional feature
    UPS_AVAILABLE = True
except Exception:
    tick_ups = None
    UPS_AVAILABLE = False

# ------------- Optional Sentience Tools -------------
_SENTIENCE_METRICS_FN = None
_SENTIENCE_TEST_FN = None
try:
    import sentience_metrics as _sm  # your file
    if hasattr(_sm, "compute_metrics"):
        _SENTIENCE_METRICS_FN = _sm.compute_metrics
except Exception:
    pass

try:
    import sentience_test as _st  # your file
    if hasattr(_st, "run_sentience_test"):
        _SENTIENCE_TEST_FN = _st.run_sentience_test
except Exception:
    pass

# ------------- World import -------------
try:
    from world import World
except Exception as e:
    print("[FATAL] Failed to import World from world.py:", e, file=sys.stderr)
    raise

# ------------- Persistence via state.py -------------
# We prefer state.world_to_dict/world_from_dict if present for full fidelity.
try:
    import state as _state
    _HAS_STATE_SAVE = hasattr(_state, "world_to_dict")
    _HAS_STATE_LOAD = hasattr(_state, "world_from_dict")
except Exception:
    _state = None
    _HAS_STATE_SAVE = _HAS_STATE_LOAD = False

# ------------- Optional history hook -------------
# If history.py defines format/transform hooks, we'll use them.
_hist_format_fn = None
_hist_post_hook = None
try:
    import history as _hist
    _hist_format_fn = getattr(_hist, "format_entry", None)
    _hist_post_hook = getattr(_hist, "on_tick_logged", None)
except Exception:
    pass

# ------------- Utilities -------------
def _read_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception as e:
            # rotate corrupt file once
            bad = HISTORY_FILE.with_suffix(".bad.json")
            HISTORY_FILE.rename(bad)
            print(f"[WARN] history.json was corrupt; moved to {bad.name}", file=sys.stderr)
    return []


def _write_json_atomic(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(obj, indent=2)
    tmp.write_text(data)
    tmp.replace(path)  # atomic on POSIX

def _write_history(history):
    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]
    _write_json_atomic(HISTORY_FILE, history)
    return history


def _snapshot(world):
    snap = {
        "tick": getattr(world, "tick", None),
        "agent_count": len(getattr(world, "agents", [])),
        "structures": len(getattr(world, "structures", [])) if hasattr(world, "structures") else 0,
        "anomalies": len(getattr(world, "anomalies", [])) if hasattr(world, "anomalies") else 0,
        "artifacts": len(getattr(world, "artifacts", [])) if hasattr(world, "artifacts") else 0,
    }
    out = SNAPSHOT_DIR / f"snapshot_tick_{str(getattr(world, 'tick', 0)).zfill(6)}.json"
    out.write_text(json.dumps(snap, indent=2))
    return str(out)


def _save_world(world):
    if _HAS_STATE_SAVE:
        try:
            data = _state.world_to_dict(world)
            SAVE_FILE.write_text(json.dumps(data))
            return
        except Exception as e:
            print("[WARN] state.world_to_dict failed; falling back to minimal save:", e)
    # fallback: minimal save so we never crash
    data = {
        "tick": getattr(world, "tick", 0),
        "structures": getattr(world, "structures", []),
        "anomalies": getattr(world, "anomalies", []),
        "artifacts": getattr(world, "artifacts", []),
    }
    SAVE_FILE.write_text(json.dumps(data))


def _load_world_or_new():
    if SAVE_FILE.exists() and _HAS_STATE_LOAD:
        try:
            data = json.loads(SAVE_FILE.read_text())
            w = _state.world_from_dict(data)
            print(f"[INFO] Loaded world from save_state.json at tick {getattr(w,'tick',0)}")
            return w
        except Exception as e:
            print("[WARN] Could not load save_state.json, starting new world:", e)
    return World()


def _sample_agents(world, k=3):
    out = []
    agents = getattr(world, "agents", [])
    for a in agents[:k]:
        info = {}
        for attr in ("id", "energy", "x", "y", "mood", "symbols", "thoughts"):
            if hasattr(a, attr):
                val = getattr(a, attr)
                if attr == "symbols" and isinstance(val, dict):
                    info["symbols"] = list(val.keys())[:6]
                elif attr == "thoughts" and isinstance(val, list):
                    info["last_thought"] = val[-1] if val else None
                else:
                    info[attr] = val
        out.append(info)
    return out


# ------------- Main loop -------------
def run(ticks=RUN_TICKS, tick_sleep=SLEEP_PER_TICK, snapshot_interval=SNAPSHOT_INTERVAL):
    world = _load_world_or_new()
    history = _read_history()

    print("[INFO] Simulation starting…")
    print(f"[INFO] Prior history entries: {len(history)}")
    print(f"[INFO] UPS: {'ENABLED' if (ENABLE_UPS and UPS_AVAILABLE) else 'DISABLED'} "
          f"(module={'present' if UPS_AVAILABLE else 'absent'}, gate={ENABLE_UPS})")
    print(f"[INFO] Sentience metrics: {'ON' if _SENTIENCE_METRICS_FN else 'OFF'}, "
          f"tests: {'ON' if _SENTIENCE_TEST_FN else 'OFF'}")

    try:
        while True:
            # advance world (use your real world/agent logic)
            if hasattr(world, "step"):
                world.step()
            else:
                world.tick = getattr(world, "tick", 0) + 1

            tick = getattr(world, "tick", 0)

            # build entry (allow history.py to transform if it wants)
            entry = {
                "tick": tick,
                "agent_count": len(getattr(world, "agents", [])),
                "structures": len(getattr(world, "structures", [])) if hasattr(world, "structures") else 0,
                "anomalies": len(getattr(world, "anomalies", [])) if hasattr(world, "anomalies") else 0,
                "artifacts": len(getattr(world, "artifacts", [])) if hasattr(world, "artifacts") else 0,
                "sample_agents": _sample_agents(world, k=3),
            }

            if _hist_format_fn:
                try:
                    entry = _hist_format_fn(entry, world)
                except Exception as e:
                    entry.setdefault("history_hook_errors", []).append({"format_entry": str(e)})

            # optional: auto sentience metrics/tests
            # --- Sentience evaluation & logging ---
            if SENTIENCE_INTERVAL and tick % SENTIENCE_INTERVAL == 0:
                sent = {}

                if _SENTIENCE_TEST_FN:
                    try:
                        s = _SENTIENCE_TEST_FN(world)
                        sent["score"] = float(s["score"] if isinstance(s, dict) and "score" in s else s)
                    except Exception as e:
                        sent["score_error"] = str(e)

                if _SENTIENCE_METRICS_FN:
                    try:
                        m = _SENTIENCE_METRICS_FN(world)  # expect dict
                        sent["metrics"] = m
                        # expose top-level metrics so jq doesn't see nulls
                        try:
                            entry.update({k: v for k, v in (m or {}).items() if k != "tick"})
                        except Exception:
                            pass
                        if "sentience_score" in m and "score" not in sent:
                            sent["score"] = float(m["sentience_score"])
                    except Exception as e:
                        sent["metrics_error"] = str(e)


                if sent:
                    if sent.get("score", 0.0) >= SENTIENCE_ALERT_THRESHOLD:
                        print(f"[SENTIENCE ALERT] tick={tick} score={sent['score']:.3f}")
                    entry["sentience"] = sent
                    try:
                        with SENTIENCE_STREAM.open("a", encoding="utf-8") as f:
                            f.write(json.dumps({"tick": tick, **sent}) + "\n")
                    except Exception:
                        pass

            # optional: UPS (kept fully off until you flip ENABLE_UPS = True)
            if ENABLE_UPS and tick_ups:
                try:
                    entry["ups"] = tick_ups(world, tick)
                except Exception as e:
                    entry["ups_error"] = str(e)

            # append & persist history
            history.append(entry)
            history = _write_history(history)

            # optional post-hook for external loggers
            if _hist_post_hook:
                try:
                    _hist_post_hook(entry, world)
                except Exception as e:
                    # non-fatal
                    pass

            # periodic snapshot + autosave
            if snapshot_interval and tick % snapshot_interval == 0:
                path = _snapshot(world)
                _save_world(world)
                print(f"[SNAPSHOT] {path} | [AUTOSAVE] save_state.json")

            # finish if fixed-length run requested
            if ticks and tick >= ticks:
                print("[INFO] Completed requested ticks; exiting.")
                break

            if tick_sleep:
                time.sleep(tick_sleep)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted. Saving & snapshotting…")
        _snapshot(world)
        _save_world(world)
        _write_history(history)
    except Exception as e:
        print("[FATAL] Unhandled exception:", e, file=sys.stderr)
        _snapshot(world)
        _save_world(world)
        _write_history(history)
        raise
    finally:
        print("[INFO] Done.")


if __name__ == "__main__":
    # CLI: python main.py [ticks] [sleep] [snapshot_interval]
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("ticks", nargs="?", type=int, default=RUN_TICKS)
    p.add_argument("sleep", nargs="?", type=float, default=SLEEP_PER_TICK)
    p.add_argument("snapshot_interval", nargs="?", type=int, default=SNAPSHOT_INTERVAL)
    args = p.parse_args()
    run(args.ticks, args.sleep, args.snapshot_interval)
