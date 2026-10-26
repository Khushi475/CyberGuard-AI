# 09 - State Transition Diagram (Behavioural Modelling)

**Project:** CyberGuard AI
**Lab experiment:** 5 - Requirement modelling using State Transition Diagram

> The transition table in this document is not a drawing made alongside the code.
> It is a description of `INCIDENT_STATE_TRANSITIONS` in
> `backend/app/models/incident.py`, which the API enforces on every request. An
> illegal transition returns HTTP 409 and is refused. The two cannot drift apart.

---

## 1. Incident lifecycle - the primary state machine

### 1.1 States

| State | Meaning | Entry condition | Terminal? |
|-------|---------|-----------------|-----------|
| **NEW** | The incident exists but nobody has started work. | Auto-opened by a CRITICAL detection, or created manually. | No |
| **OPEN** | Acknowledged and queued for an analyst. | An analyst accepts it without starting active investigation. | No |
| **INVESTIGATING** | An analyst is actively working the case. | Analyst begins triage. | No |
| **CONTAINED** | The threat has been limited but the case is not closed. | Containment applied (block, isolate, rate-limit). | No |
| **RESOLVED** | Handled and verified; the case is closed. | Containment confirmed effective. | Yes (reopenable) |
| **FALSE_POSITIVE** | The activity was legitimate. | Analyst determines the detection was wrong. | Yes (reopenable) |

### 1.2 State transition diagram

```
                             (detection engine, risk >= 76)
                             (or manual creation by analyst)
                                          |
                                          v
                                   +--------------+
                                   |     NEW      |
                                   +--------------+
                                    |     |      |
                   acknowledge      |     |      |      dismiss
                        +-----------+     |      +-----------------+
                        |                 | begin                  |
                        v                 | triage                 |
                 +--------------+         |                        |
                 |     OPEN     |         |                        |
                 +--------------+         |                        |
                  |      |     |          |                        |
       begin      |      |     | dismiss  |                        |
       triage     |      |     +----------|------------+           |
                  |      |                |            |           |
                  |      | contain        |            |           |
                  |      | directly       |            |           |
                  |      |                |            |           |
                  v      |                v            |           |
              +----------------------------------+     |           |
              |          INVESTIGATING           |<----+-----------+
              +----------------------------------+   reopen      reopen
                  |            |            |          ^            ^
         contain  |            | resolve    | dismiss  |            |
                  |            | directly   |          |            |
                  v            |            |          |            |
          +--------------+     |            |          |            |
          |  CONTAINED   |     |            |          |            |
          +--------------+     |            |          |            |
              |      |         |            |          |            |
      resolve |      | reopen  |            |          |            |
              |      +---------|------------|----------+            |
              |                |            |                       |
              v                v            v                       |
          +--------------------------+   +--------------------------+
          |        RESOLVED          |   |     FALSE_POSITIVE       |
          +--------------------------+   +--------------------------+
                      |                              |
                      | reopen                       | reopen
                      +------------> INVESTIGATING <-+
```

### 1.3 Transition table (the executable specification)

| From | Event / action | To | Guard | Side effects |
|------|----------------|----|-------|--------------|
| (none) | Detection risk >= 76 | NEW | `auto_incident` enabled | Incident created; `INC-` code assigned; alert linked; history seeded |
| (none) | Analyst creates manually | NEW | Title and severity valid | Incident created; assignee defaults to the acting user |
| NEW | acknowledge | OPEN | - | History appended |
| NEW | begin triage | INVESTIGATING | - | History appended |
| NEW | dismiss | FALSE_POSITIVE | - | `resolved_at` stamped; child alerts marked FALSE_POSITIVE |
| OPEN | begin triage | INVESTIGATING | - | History appended |
| OPEN | contain directly | CONTAINED | - | `contained_at` stamped |
| OPEN | dismiss | FALSE_POSITIVE | - | `resolved_at` stamped; child alerts closed |
| INVESTIGATING | contain | CONTAINED | - | `contained_at` stamped |
| INVESTIGATING | resolve directly | RESOLVED | - | `resolved_at` stamped; resolution summary stored; child alerts RESOLVED |
| INVESTIGATING | dismiss | FALSE_POSITIVE | - | `resolved_at` stamped; child alerts FALSE_POSITIVE |
| CONTAINED | resolve | RESOLVED | - | `resolved_at` stamped; child alerts RESOLVED |
| CONTAINED | reopen | INVESTIGATING | - | `resolved_at` cleared |
| RESOLVED | reopen | INVESTIGATING | - | `resolved_at` cleared |
| FALSE_POSITIVE | reopen | INVESTIGATING | - | `resolved_at` cleared |

### 1.4 Explicitly forbidden transitions

Any transition not in the table above is refused with **HTTP 409 CONFLICT**,
and the response states the current state and the permitted set.

| Attempted | Why it is forbidden |
|-----------|---------------------|
| NEW -> CONTAINED | Nothing can be contained before anyone has looked at it. Triage must happen first. |
| NEW -> RESOLVED | Closing a case nobody investigated would defeat the audit trail. |
| OPEN -> RESOLVED | Same reason: resolution must follow investigation or containment. |
| CONTAINED -> FALSE_POSITIVE | If containment was already applied, the finding was acted on; retroactively calling it a false positive would misstate the history. Reopen and investigate instead. |
| RESOLVED -> CONTAINED | Cannot regress from closed to a mid-lifecycle state; reopen to INVESTIGATING first. |
| RESOLVED -> FALSE_POSITIVE | Would rewrite the outcome of a closed case. Reopen first. |

### 1.5 Source of truth

```python
# backend/app/models/incident.py
INCIDENT_STATE_TRANSITIONS = {
    "NEW":            {"OPEN", "INVESTIGATING", "FALSE_POSITIVE"},
    "OPEN":           {"INVESTIGATING", "CONTAINED", "FALSE_POSITIVE"},
    "INVESTIGATING":  {"CONTAINED", "RESOLVED", "FALSE_POSITIVE"},
    "CONTAINED":      {"RESOLVED", "INVESTIGATING"},
    "RESOLVED":       {"INVESTIGATING"},
    "FALSE_POSITIVE": {"INVESTIGATING"},
}
```

The API returns the currently legal set on every incident read
(`state_machine.allowed`), and the Incident Details page renders **only** those
buttons. The UI therefore cannot offer an illegal move, and the API would refuse
it even if it did.

### 1.6 Verification

| Test | Property verified |
|------|-------------------|
| `test_incident_exposes_only_legal_transitions` | From NEW, exactly {OPEN, INVESTIGATING, FALSE_POSITIVE} is offered |
| `test_illegal_transition_is_refused` | NEW -> RESOLVED returns 409 with the current state and allowed set |
| `test_full_lifecycle_new_to_resolved` | NEW -> INVESTIGATING -> CONTAINED -> RESOLVED succeeds and records 4 history entries |
| `test_incident_can_be_closed_as_false_positive` | The dismissal path works and stores the resolution summary |
| `test_resolving_an_incident_closes_its_alerts` | Terminal transitions cascade to child alerts |

---

## 2. Alert lifecycle - secondary state machine

Alerts have their own, simpler machine. An alert is a notification; an incident
is an investigation. Several alerts may belong to one incident.

### 2.1 States

| State | Meaning |
|-------|---------|
| **NEW** | Raised by the engine; not yet seen. |
| **ACKNOWLEDGED** | An analyst has seen it but not acted. |
| **INVESTIGATING** | Being worked, usually as part of an incident. |
| **RESOLVED** | Confirmed as a genuine finding and handled. |
| **FALSE_POSITIVE** | Determined to be legitimate activity. |

### 2.2 Diagram

```
        (detection engine, risk >= 26)
                     |
                     v
              +-------------+
              |     NEW     |
              +-------------+
               |    |     |  \
   acknowledge |    |     |   \  mark false positive
               v    |     |    \
      +--------------+   |      \
      | ACKNOWLEDGED |   |       \
      +--------------+   | resolve\
          |       |      | direct  \
investigate|      |      |          \
          v       |      v           v
   +---------------+   +----------+  +------------------+
   | INVESTIGATING |-->| RESOLVED |  | FALSE_POSITIVE   |
   +---------------+   +----------+  +------------------+
          ^   |              |                |
          |   | mark false   | reopen         | reopen
          |   | positive     |                |
          |   +----------> FALSE_POSITIVE     |
          |                  |                |
          +------------------+----------------+
```

### 2.3 Transition table

| From | Allowed next states |
|------|---------------------|
| NEW | ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE |
| ACKNOWLEDGED | INVESTIGATING, RESOLVED, FALSE_POSITIVE |
| INVESTIGATING | RESOLVED, FALSE_POSITIVE, ACKNOWLEDGED |
| RESOLVED | INVESTIGATING (reopen) |
| FALSE_POSITIVE | INVESTIGATING (reopen) |

Source: `ALERT_STATUS_TRANSITIONS` in `backend/app/models/alert.py`.

### 2.4 Why the alert machine is more permissive

An alert may legitimately be resolved straight from NEW - an experienced analyst
can recognise a known-benign pattern at a glance and close it without a formal
investigation. An **incident**, by contrast, represents a case that has been
opened precisely because it needs work, so skipping investigation would make the
audit trail meaningless.

This asymmetry is deliberate and is the reason the two machines are separate
rather than shared.

### 2.5 Feedback loop into detection quality

The two terminal alert states are not merely bookkeeping. They are the system's
ground-truth signal:

```
precision = RESOLVED / (RESOLVED + FALSE_POSITIVE)
```

Once five or more alerts have reached a terminal state, this becomes the
"Detection Accuracy" figure on the dashboard, labelled **analyst-confirmed
precision**. Before that threshold the system says so and falls back to the
model's synthetic hold-out score, explicitly labelled as such
(`analytics_service.detection_quality`).

---

## 3. Security event processing states

A minor machine, but it documents the `processed` flag on `SecurityEvent`.

```
    +-------------+   validation passes   +-------------+
    |  SUBMITTED  |---------------------->|  VALIDATED  |
    +-------------+                       +-------------+
           |                                     |
           | validation fails                    | detection engine runs
           v                                     v
    +-------------+                       +-------------+
    |  REJECTED   |                       |  ANALYSED   |
    | (HTTP 422,  |                       | processed = |
    |  not stored)|                       |    true     |
    +-------------+                       +-------------+
                                                 |
                                   +-------------+-------------+
                                   |                           |
                            is_threat = false           is_threat = true
                                   |                           |
                                   v                           v
                            +-------------+            +-------------+
                            |    BENIGN   |            |  THREAT     |
                            | (no alert)  |            |  RECORDED   |
                            +-------------+            +-------------+
                                                              |
                                                     risk >= 26 -> alert
                                                     risk >= 76 -> incident
```

A rejected event is **never stored**. This keeps the analytics clean: every row
in `security_events` is a record that passed validation, so aggregate counts are
meaningful without filtering.

---

## 4. Asset risk-level states

An asset's risk level is derived, not set by hand (though an administrator may
override it).

```
     +-------+  event risk 26-50   +----------+  event risk 51-75  +--------+
     |  LOW  |-------------------->|  MEDIUM  |------------------->|  HIGH  |
     +-------+                     +----------+                    +--------+
         ^                                                              |
         |                                                              | event
         | administrator override / re-seed                             | risk
         |                                                              | >= 76
         |                          +--------------+                    |
         +--------------------------|   CRITICAL   |<-------------------+
                                    +--------------+
```

Rule: an asset's `risk_score` only ever **increases** through observation
(`_update_asset_risk` keeps the maximum). It is reduced only by an explicit
administrator action or by re-seeding. This is intentional - an asset that was
attacked yesterday is still a host of concern today, and silently decaying its
risk would hide that.

Separately, an asset has an **operational status** (ONLINE, OFFLINE, MAINTENANCE,
QUARANTINED) which is set by an administrator and is independent of risk level.

---

## 5. Session state (client side)

```
   +---------------+  successful login   +--------------+
   | UNAUTHENTICATED|------------------->| AUTHENTICATED |
   +---------------+                     +--------------+
        ^     ^                            |    |     |
        |     |          explicit logout   |    |     |
        |     +----------------------------+    |     |
        |                                       |     | backend unreachable
        |         any endpoint returns 401      |     |
        +---------------------------------------+     v
                                              +------------------+
                                              | AUTHENTICATED    |
                                              | (degraded)       |
                                              | cached session   |
                                              | kept; errors     |
                                              | shown per page   |
                                              +------------------+
```

The degraded state matters for usability. If the Flask process is simply not
running, the analyst is **not** signed out - the session is kept and each page
shows a "Backend unavailable" state with the exact command to start it. Only a
genuine HTTP 401 clears the session (`AuthContext`, `setUnauthorizedHandler`).

---

## 6. Traceability

| Lab requirement | Where satisfied |
|-----------------|-----------------|
| Incident lifecycle NEW -> OPEN -> INVESTIGATING -> CONTAINED -> RESOLVED | Section 1.2 |
| FALSE_POSITIVE supported | Sections 1.2, 1.3, 2.2 |
| Valid transitions shown clearly | Transition tables 1.3 and 2.3 |
| Invalid transitions identified | Section 1.4 |
| Behaviour enforced, not just drawn | Section 1.5 and the tests in Section 1.6 |
