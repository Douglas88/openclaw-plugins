# Test Patterns Reference

## The Test Pyramid

```
        ╱  E2E  ╲        — fewest, slowest, most expensive
       ╱──────────╲
      ╱ Integration ╲     — medium count, medium speed
     ╱────────────────╲
    ╱   Unit Tests     ╲  — most numerous, fastest, cheapest
   ╱──────────────────────╲
```

- **Unit tests** (70%): Test individual functions/methods in isolation. Mock all dependencies.
- **Integration tests** (20%): Test interactions between modules. Real DB, real HTTP (or in-memory fakes).
- **E2E tests** (10%): Full user flows. Real browser or API client. Slowest, most brittle.

## Fixture Patterns

### Inline fixture (simple, explicit)
```python
@pytest.fixture
def user():
    return User(name="Test", email="test@example.com")
```

### Factory fixture (parametric)
```python
@pytest.fixture
def make_user():
    def _make(name="Test", admin=False):
        return User(name=name, is_admin=admin)
    return _make

def test_admin(make_user):
    admin = make_user(admin=True)
    assert admin.is_admin
```

### Session-scoped fixture (expensive setup, shared)
```python
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

## Mock Patterns

| Pattern | When to use | Python | Jest |
|---------|-------------|--------|------|
| **Function mock** | Replace single function | `mocker.patch("mod.func")` | `jest.fn()` / `jest.spyOn()` |
| **Module mock** | Replace entire import | `mocker.patch("mymod")` | `jest.mock("./module")` |
| **Object mock** | Fake class instance | `mocker.MagicMock()` | `jest.fn()` with methods |
| **HTTP mock** | Stub network calls | `responses` / `httpx-mock` | `msw` / `nock` |
| **File I/O mock** | Fake filesystem reads | `mocker.patch("builtins.open")` | `jest.mock("fs")` |

### Golden rule: Mock only what you own
Mock at the boundary of your code and external systems. Don't mock internal helpers.

## Parametrized Test Patterns

### Pytest: same logic, different inputs
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
    ("你好", 2),
    ("a b", 3),
], ids=["english", "empty", "chinese", "spaces"])
def test_strlen(input, expected):
    assert len(input) == expected
```

### Jest: `it.each` / `test.each`
```typescript
it.each([
  ['hello', 5],
  ['', 0],
  ['你好', 2],
])('%s has length %i', (input, expected) => {
  expect(input.length).toBe(expected);
});
```

### Go: table-driven (idiomatic)
```go
tests := []struct{ name, input string; want int }{
    {"english", "hello", 5},
    {"empty", "", 0},
    {"unicode", "你好", 2},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        if got := len(tt.input); got != tt.want {
            t.Errorf("len(%q) = %d, want %d", tt.input, got, tt.want)
        }
    })
}
```

## Snapshot Testing

Snapshots capture the full output of a function and detect unintended changes.

**When to use:** Rendering output (HTML, JSON, serialized structs), complex objects where writing assertions is tedious.

**When NOT to use:** Unstable output (timestamps, random IDs), large blobs, data that changes frequently.

### Jest Snapshots
```typescript
it('renders user card correctly', () => {
  const html = renderUserCard({ name: 'Alice', role: 'admin' });
  expect(html).toMatchSnapshot();
});
```

### Pytest (syrupy / snapshottest)
```python
def test_api_response(snapshot):
    response = client.get("/api/users/1")
    assert response.json() == snapshot
```

Always review snapshot diffs before committing. "Update snapshots" is not a fix.
