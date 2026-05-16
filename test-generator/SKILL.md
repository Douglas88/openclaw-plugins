---
name: test-generator
description: Automated test generation for Python (pytest), JavaScript/TypeScript (jest), Go (testing). Use when: (1) generating unit tests for existing code, (2) adding test coverage, (3) creating test fixtures, (4) generating mock objects. Analyzes source code to create tests covering normal cases, edge cases, error handling, and boundary conditions.
version: "1.0.0"
---

# Test Generator

Generate unit tests from source code for Python, JavaScript/TypeScript, and Go.

## Workflow

1. **Analyze source** — read the target file, identify functions/methods, their signatures, dependencies, and return types
2. **Identify testable units** — public functions, methods, exported symbols; note external dependencies that need mocking
3. **Generate test file** — place tests alongside source (e.g., `src/foo.py` → `tests/test_foo.py`) or in a `__tests__/` directory
4. **Confirm framework & coverage target** before generating — ask if not specified

### Quick-start template (ask the user):

```
What framework? pytest | jest | go test
What coverage target? 80% | 90% | 100%
Any specific functions to focus on, or all?
```

---

## Python (pytest)

### Detection
- `import pytest` or `pytest` in dev dependencies
- Test files: `test_*.py` or `*_test.py`
- Common patterns: fixtures, `@pytest.mark.parametrize`, `unittest.mock`

### Generation Pattern

Given this source (`calculator.py`):
```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

Generate:
```python
# tests/test_calculator.py
import pytest
from calculator import divide

class TestDivide:
    def test_normal_division(self):
        assert divide(10, 2) == 5.0
        assert divide(7, 2) == 3.5

    def test_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(1, 0)

    @pytest.mark.parametrize("a,b,expected", [
        (0, 5, 0),        # zero numerator
        (-10, 2, -5),     # negative
        (1, 3, 1/3),      # repeating decimal
        (1e100, 1e-100, 1e200),  # extreme values
    ])
    def test_edge_cases(self, a, b, expected):
        assert divide(a, b) == pytest.approx(expected)

    def test_divide_with_mock(self, mocker):
        # Demonstrate mock for external dependency
        mock_db = mocker.patch("mymodule.db.get_value", return_value=42)
        result = process_with_db(10)
        mock_db.assert_called_once()
        assert result == 420
```

### Fixtures
```python
import pytest

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}

@pytest.fixture
def db_session():
    """Create a test database session, rollback after test."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

def test_user_creation(sample_user, db_session):
    user = User(**sample_user)
    db_session.add(user)
    assert user.id is not None
```

### Coverage
```bash
# Install pytest-cov, then:
pytest --cov=src/ --cov-report=term --cov-report=html
# Target: --cov-fail-under=80
```

---

## JavaScript / TypeScript (Jest)

### Detection
- `jest` in `package.json` or `jest.config.*`
- Test files: `*.test.ts`, `*.spec.ts`, `__tests__/*.ts`
- Mock patterns: `jest.fn()`, `jest.mock()`, `jest.spyOn()`

### Generation Pattern

Given this source (`utils/parser.ts`):
```typescript
export function parseJSON<T>(raw: string): T {
  try {
    return JSON.parse(raw) as T;
  } catch (e) {
    throw new Error(`Invalid JSON: ${(e as Error).message}`);
  }
}
```

Generate:
```typescript
// utils/__tests__/parser.test.ts
import { parseJSON } from '../parser';

describe('parseJSON', () => {
  it('parses valid JSON object', () => {
    expect(parseJSON('{"a":1}')).toEqual({ a: 1 });
  });

  it('parses array JSON', () => {
    expect(parseJSON('[1,2,3]')).toEqual([1, 2, 3]);
  });

  it('throws on invalid JSON', () => {
    expect(() => parseJSON('{bad')).toThrow('Invalid JSON:');
  });

  it('throws on empty string', () => {
    expect(() => parseJSON('')).toThrow('Invalid JSON:');
  });

  it('parses null and primitives', () => {
    expect(parseJSON('null')).toBeNull();
    expect(parseJSON('42')).toBe(42);
    expect(parseJSON('"hello"')).toBe('hello');
  });
});
```

### Async & Mock Functions
```typescript
// Testing async code
import { fetchUser } from '../api';

describe('fetchUser', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns user data on success', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, name: 'Bob' }),
    });

    const user = await fetchUser(1);
    expect(user).toEqual({ id: 1, name: 'Bob' });
    expect(global.fetch).toHaveBeenCalledWith('/api/users/1');
  });

  it('throws on HTTP error', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    await expect(fetchUser(999)).rejects.toThrow('404');
  });
});
```

### Coverage
```bash
jest --coverage
# Config in jest.config.ts:
# coverageThreshold: { global: { branches: 80, functions: 80, lines: 80 } }
```

---

## Go (testing)

### Detection
- `*_test.go` files
- `import "testing"` or testify
- Table-driven tests are idiomatic

### Generation Pattern

Given this source (`pkg/math/ops.go`):
```go
package math

import "errors"

func Divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("cannot divide by zero")
    }
    return a / b, nil
}
```

Generate:
```go
// pkg/math/ops_test.go
package math

import (
    "testing"
)

func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    float64
        want    float64
        wantErr bool
    }{
        {"normal division", 10, 2, 5.0, false},
        {"fractional result", 7, 3, 2.3333333333333335, false},
        {"zero numerator", 0, 5, 0, false},
        {"negative dividend", -10, 2, -5, false},
        {"negative divisor", 10, -2, -5, false},
        {"both negative", -10, -2, 5, false},
        {"divide by zero", 1, 0, 0, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Divide(tt.a, tt.b)
            if tt.wantErr {
                if err == nil {
                    t.Errorf("Divide(%v, %v) expected error, got nil", tt.a, tt.b)
                }
                return
            }
            if err != nil {
                t.Errorf("Divide(%v, %v) unexpected error: %v", tt.a, tt.b, err)
                return
            }
            if got != tt.want {
                t.Errorf("Divide(%v, %v) = %v, want %v", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

### Interfaces & Mocking
```go
// Use interface for dependency injection, then mock in tests
type UserStore interface {
    GetUser(id int) (*User, error)
}

type mockUserStore struct {
    user *User
    err  error
}

func (m *mockUserStore) GetUser(id int) (*User, error) {
    return m.user, m.err
}

func TestGetUserName(t *testing.T) {
    store := &mockUserStore{user: &User{Name: "Alice"}}
    name, err := GetUserName(store, 1)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if name != "Alice" {
        t.Errorf("got %q, want %q", name, "Alice")
    }
}
```

### Coverage
```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out  # open in browser
go test -cover -coverpkg=./... ./...  # cross-package coverage
```

---

## Test Generation Checklist

For each function/method, generate tests for:

| Category | What to test |
|----------|-------------|
| **Normal case** | Typical input → expected output |
| **Boundary** | Empty input, zero, max/min values, nil/null |
| **Error** | Invalid input, missing required fields, external failure |
| **Edge** | Large inputs, concurrency, special characters |
| **Mock** | External calls (DB, HTTP, filesystem) are mocked |

Ask before generating if:
- Framework choice is ambiguous
- Coverage target not specified
- Test directory convention differs from project standard

See `references/test_patterns.md` for deeper patterns: test pyramid, fixtures, mocks, parametrize, snapshots.
