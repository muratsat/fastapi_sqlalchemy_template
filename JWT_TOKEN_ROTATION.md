```
TIME ──────────────────────────────────────────────────────►

USER                    CLIENT                  SERVER
 │                        │                        │
 │  1. LOGIN              │                        │
 ├──────────────────────► │                        │
 │                        │  2. AUTH REQUEST       │
 │                        ├──────────────────────► │
 │                        │                        │ 3. VALIDATE
 │                        │                        │    GENERATE TOKENS
 │                        │  4. ACCESS + REFRESH   │
 │                        │◄───────────────────────┤
 │                        │                        │
 │                        │ [RT stored secure]     │
 │                        │ [AT in memory]         │
 │                        │                        │
 │  5. USE RESOURCE       │                        │
 ├───────────────────────►│                        │
 │                        │  6. REQUEST + AT       │
 │                        ├───────────────────────►│
 │                        │  7. RESOURCE           │ [AT valid]
 │                        │◄───────────────────────┤
 │  8. RESPONSE           │                        │
 │◄───────────────────────┤                        │
 │                        │                        │
 │    ... TIME PASSES ... │                        │
 │    [AT EXPIRES]        │                        │
 │                        │                        │
 │  9. USE RESOURCE       │                        │
 ├ ──────────────────────►│                        │
 │                        │  10. REQUEST + AT      │
 │                        ├───────────────────────►│
 │                        │  11. 401 EXPIRED       │ [AT expired]
 │                        │◄───────────────────────┤
 │                        │                        │
 │                        │ [AUTO: ROTATION]       │
 │                        │  12. RT ONLY           │
 │                        ├───────────────────────►│
 │                        │                        │ 13. VALIDATE RT
 │                        │                        │     INVALIDATE OLD RT
 │                        │                        │     GENERATE NEW PAIR
 │                        │  14. NEW AT + NEW RT   │
 │                        │◄───────────────────────┤
 │                        │                        │
 │                        │ [store new RT]         │
 │                        │ [new AT in memory]     │
 │                        │                        │
 │                        │  15. RETRY + NEW AT    │
 │                        ├───────────────────────►│
 │                        │  16. RESOURCE          │ [new AT valid]
 │                        │◄───────────────────────┤
 │  17. RESPONSE          │                        │
 │◄───────────────────────┤                        │


COMPROMISE SCENARIO:
─────────────────────

ATTACKER              SERVER
   │                    │
   │  OLD RT (stolen)   │
   ├───────────────────►│
   │                    │ [RT already used = ALERT]
   │  REJECT            │ [Invalidate entire token family]
   │◄───────────────────┤
   │                    │
                        │
                     LEGITIMATE USER
                        │  ANY RT from family
                        ├───────────────────►│
                        │  REJECT - REAUTH   │ [Family dead]
                        │◄───────────────────┤


TOKEN STATES:
─────────────

AT Lifespan:  [████░░░░░░] 5-15 min
RT Lifespan:  [██████████] days/weeks

Each rotation:
  RT(n) ──[used]──► RT(n+1) + AT(new)
            └──[DEAD]
```
