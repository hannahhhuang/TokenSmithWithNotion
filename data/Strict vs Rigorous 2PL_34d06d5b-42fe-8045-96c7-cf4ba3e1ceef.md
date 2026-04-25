## **Strict Two-Phase Locking**

1. **Definition:** A transaction must hold all its exclusive locks till it commits/aborts.
2. **Advantages:**
1. Ensures recoverability.
  2. Avoids cascading roll-backs.
3. **Implementation considerations:** Requires careful lock management at the system level.
## **Rigorous Two-Phase Locking**

1. **Definition:** A transaction must hold all locks till commit/abort.
2. **Key Properties:**
1. Transactions can be serialized in the order in which they commit.
  2. Stricter than Strict 2PL because it applies to *all* locks, not just exclusive ones.