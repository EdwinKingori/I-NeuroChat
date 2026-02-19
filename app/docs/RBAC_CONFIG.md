# RBAC Configuration for INeuroChat API

This document explains **how Role-Based Access Control (RBAC)** works in the **INeuroChat API**, how it connects to the **session-based authentication** system, and how permissions are enforced across routes (including admin routes).



---

## 1. What RBAC Is (In Plain Terms)

**RBAC = Role-Based Access Control**

Instead of hardcoding logic like:
- `is_admin = True/False`

…RBAC uses:
- **Roles** (e.g., `admin`, `support`, `user`)
- **Permissions** (e.g., `users.read`, `users.activate`)
- A mapping that decides:
  - which roles have which permissions
  - which users have which roles

### Why RBAC is better than `is_admin`
| Boolean Admin Flag | RBAC |
|---|---|
| Only “admin or not” | Many roles possible |
| Hard to add new admin types | Add roles like `support`, `moderator`, `analyst` |
| Permissions are implicit | Permissions are explicit and auditable |
| Changing access requires code changes | Changing access can be data-driven (roles/permissions) |


---

## 2. RBAC Components (Tables + What They Mean)

RBAC in INeuroChat uses **4 core tables**:

### 2.1 `roles`
Stores the roles supported by the system.

**Examples**
- `admin`
- `support`
- `user`

**What it answers**
- “What kinds of roles exist?”

---

### 2.2 `permissions`
Stores the **atomic actions** that can be allowed/denied.

**Examples**
- `users.read`
- `users.activate`
- `users.promote`

**What it answers**
- “What actions does the API recognize as controllable?”

---

### 2.3 `role_permissions`
A many-to-many mapping of **roles → permissions**.

**What it answers**
- “What can this role do?”

Example:
- `admin` → can `users.read`, `users.activate`, `users.promote`
- `support` → can `users.read`
- `user` → None given

---

### 2.4 `user_roles`
A many-to-many mapping of **users → roles**.

**What it answers**
- “What roles does this user have?”

Example:
- John → `user`
- Mary → `support`
- Alice → `admin`

---

## 3. Authentication vs Authorization (Important Difference)

### 3.1 Authentication: “Who are you?”
In INeuroChat, authentication is done using a **session_key**.

- The client sends a `session_key` in request headers
- The API validates it (Redis first, DB fallback)
- If valid, the API identifies the user: `user_id`

✅ Authentication result:  
> “This request is made by user XYZ.”

---

### 3.2 Authorization: “What are you allowed to do?”
RBAC is the authorization system.

After authentication is successful:
- RBAC checks if the user has the required permission
- If yes → proceed
- If no → `403 Forbidden`

✅ Authorization result:  
> “User XYZ has permission to do this action.”

---

## 4. Process Flow: From Request → Permission Check

This is the full flow for a protected endpoint.

### Step 1 — Client sends request with session_key
Example:

```
GET /api/v1/admin/users
session_key: abc123...
```

---

### Step 2 — `get_current_user()` authenticates the request
**Auth dependency** checks:
1. Redis lookup: `session:{session_key}`
2. DB fallback if cache miss
3. Rejects if inactive/expired

Return payload (typical):
```json
{
  "user_id": "uuid-of-user",
  "is_active": true
}
```

---

### Step 3 — `require_permission("users.read")` authorizes the request
**Permission dependency** does:
1. Fetch user from DB
2. Load user's roles
3. Load role permissions
4. Check required permission exists in the set

If permission is missing:
- returns `403 Insufficient permissions`

---

### Step 4 — Route executes
Only after both checks pass:
- the endpoint runs
- data is returned

---

## 5. How Admin Works in RBAC (No `is_admin`)

In INeuroChat, **admin is a role**, not a boolean field.

- A user becomes “admin” by being assigned the `admin` role
- The `admin` role has powerful permissions

### Example Admin Permissions
Common permissions for admin routes:
- `users.read` → list users
- `users.activate` → activate/deactivate users
- `users.promote` → assign roles (admin promotion)

This means:
- you can create multiple admin tiers in future (e.g., `superadmin`, `moderator`)
- without changing the authentication design

---

## 6. Default Role Assignment (Security Requirement)

**Users must never choose their own roles.**

When a user registers:
- the API should automatically assign the default role: `user`

### Recommended registration flow
1. Create user in DB
2. Assign role `"user"` using `CRUDHelper.assign_role(user_id, "user")`

This prevents attackers from trying:
```json
{ "role": "admin" }
```

The API should ignore any role fields from the client.

---

## 7. Promoting a User to Admin (Admin Workflow)

Promotion is implemented by role assignment:

1. An authorized admin calls:
   - `PATCH /api/v1/admin/users/{user_id}/promote`

2. Route is protected by:
   - `require_permission("users.promote")`

3. Route logic assigns:
   - `CRUDHelper.assign_role(user_id, "admin")`

4. Assignment is idempotent:
   - if the user already has admin role, it does nothing (safe)

---

## 8. Seeding RBAC Data (First-time Setup)

RBAC needs initial data:
- roles
- permissions
- role-permission mappings

This is done via seed scripts:
- `seed_map_definitions.py` (declarative config)
- `rbac_seed.py` (execution logic)

**Order**
1. Run Alembic migrations first (create tables)
2. Run seed script second (insert rows)

---

## 9. User Lifecycle + Security Policy (Active/Inactive)

INeuroChat uses:
- `users.is_active` → account status
- `users.last_login` → last access timestamp (UTC)

### Why this exists
- to disable stale accounts (security best practice)
- to control access if a user is banned or inactive

### Background task (Celery)
A scheduled task can deactivate users who haven’t logged in for 90 days.

This does not replace RBAC — it complements security:
- inactive user should fail auth/authorization checks

---

## 10. Redis Security Note: User-Scoped Cache Keys

To reduce risk of cache leakage and cross-user collisions:
- cache keys should include user identity where appropriate

Example safer patterns:
- `message:{user_id}:{message_id}`
- `sessions:list:{user_id}:{page}:{limit}:{sort_by}:{order}`

This ensures:
- user A cannot accidentally read user B’s cached data
- cache invalidation is scoped safely

---

## 11. Practical Examples

### Example A: Normal user tries to list all users
Request:
- `GET /api/v1/admin/users`

Required permission:
- `users.read`

Normal user roles:
- `user` → no `users.read`

Result:
- **403 Forbidden**

---

### Example B: Support role lists users
Support roles:
- `support`
Support permissions:
- `users.read`

Result:
- **200 OK**

---

### Example C: Admin promotes another user
Admin permissions:
- `users.promote`

Action:
- Assign `admin` role in `user_roles`

Result:
- user gains new access immediately

---

## 12. Extension Plan (Future RBAC Improvements)

RBAC can grow cleanly:
- Add role categories (e.g., tenant-based roles)
- Add resource-scoped permissions (e.g., per-project)
- Add audit logging for sensitive admin actions
- Add Redis permission caching per user for speed

---

## 13. Summary

RBAC in INeuroChat:
- separates **identity** (auth) from **access control** (authorization)
- replaces `is_admin` with scalable role/permission design
- ensures users cannot self-assign privileges
- supports enterprise growth without redesigning auth

If you need help documenting your exact permission list, seeding strategy, or adding audit logs, this RBAC foundation is the right base.
