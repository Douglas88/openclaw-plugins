# Security Anti-Patterns Reference

## SQL Injection (🔴 CRITICAL)

### Vulnerable
```python
# ❌ String formatting
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)

# ❌ String concatenation
query = "SELECT * FROM users WHERE name = '" + name + "'"
```

### Fixed
```python
# ✅ Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ✅ ORM with proper escaping
User.objects.filter(id=user_id)
```

---

## XSS (🔴 CRITICAL)

### Vulnerable
```python
return f"<div>{user_input}</div>"
```

```javascript
element.innerHTML = userInput;  // ❌
```

### Fixed
```python
# ✅ Escape
from markupsafe import escape
return f"<div>{escape(user_input)}</div>"
```

```javascript
element.textContent = userInput;  // ✅
```

---

## Command Injection (🔴 CRITICAL)

### Vulnerable
```python
# ❌
os.system(f"rm {filename}")
subprocess.run(f"ls {path}", shell=True)
eval(user_code)
```

### Fixed
```python
# ✅
import shlex
subprocess.run(["ls", path])
ast.literal_eval(user_code)  # Only for literals
```

---

## Hardcoded Secrets (🔴 CRITICAL)

### Vulnerable
```python
API_KEY = "sk-abc123..."           # ❌ In code
DATABASE_URL = "postgresql://..."  # ❌ In code
```

### Fixed
```python
# ✅ From env
import os
API_KEY = os.environ.get("API_KEY")
```

---

## Path Traversal (🟡 HIGH)

### Vulnerable
```python
filepath = os.path.join("/var/www", user_filename)  # ❌ ../../etc/passwd
```

### Fixed
```python
# ✅
safe_path = os.path.realpath(os.path.join("/var/www", user_filename))
if not safe_path.startswith("/var/www"):
    raise ValueError("Path traversal detected")
```

---

## Insecure Deserialization (🟡 HIGH)

### Vulnerable
```python
data = pickle.loads(user_input)     # ❌ RCE
data = yaml.load(user_input)        # ❌ RCE
```

### Fixed
```python
import json
data = json.loads(user_input)             # ✅
data = yaml.safe_load(user_input)         # ✅
```

---

## N+1 Query (🟡 HIGH)

### Vulnerable
```python
# ❌ N+1
users = User.objects.all()
for user in users:
    print(user.profile.city)  # 1 query per user
```

### Fixed
```python
# ✅ Eager loading
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.city)  # Single query
```
