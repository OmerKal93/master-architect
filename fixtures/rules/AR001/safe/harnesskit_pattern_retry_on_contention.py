# Regression fixture (found via independent dogfood review against real HarnessKit code):
# Python mirror of scripts/review-independence/run-json-atomic.js's retryOnContention() (JS),
# a confirmed false positive. A while True: retry loop whose bound is a compound condition
# (`not is_contended(e) or time.time() >= deadline`) exiting via `raise`, not a bare
# `if <comparison>: break/return`. Proves the widened _has_visible_step_bound heuristic
# (_test_contains_bound_comparison + raise-as-exit) now recognizes it as bounded.
def retry_on_contention(fn, deadline):
    while True:
        try:
            return fn()
        except Exception as e:
            if not is_contended(e) or time.time() >= deadline:
                raise
            sleep(0.05)
