"""
Minimal stand-in for pytest so these tests actually execute in a
network-isolated sandbox. In your real environment, just use:
    python -m pytest tests/ -v
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import types

# Fake a minimal `pytest` module providing pytest.raises, since the real
# package can't be installed here (no network egress).
class _RaisesContext:
    def __init__(self, exc_type):
        self.exc_type = exc_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"Expected {self.exc_type.__name__} but no exception was raised")
        if not issubclass(exc_type, self.exc_type):
            return False
        return True


fake_pytest = types.ModuleType("pytest")
fake_pytest.raises = _RaisesContext
fake_pytest.main = lambda *a, **k: 0
sys.modules["pytest"] = fake_pytest

import importlib
test_mod = importlib.import_module("tests.test_truthlock")

test_fns = [
    (name, fn) for name, fn in vars(test_mod).items()
    if name.startswith("test_") and callable(fn)
]

passed, failed = 0, 0
for name, fn in test_fns:
    try:
        fn()
        print(f"PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"FAIL  {name}: {e}")
        traceback.print_exc()
        failed += 1

print(f"\n{passed} passed, {failed} failed out of {len(test_fns)}")
sys.exit(1 if failed else 0)
