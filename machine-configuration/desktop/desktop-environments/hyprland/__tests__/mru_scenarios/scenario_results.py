class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name: str):
        self.passed += 1
        print(f"  PASS: {name}")

    def fail(self, name: str, detail: str):
        self.failed += 1
        self.errors.append(f"{name}: {detail}")
        print(f"  FAIL: {name} — {detail}")

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.ok(name)
        else:
            self.fail(name, detail)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailures:")
            for e in self.errors:
                print(f"  - {e}")
        return self.failed == 0
