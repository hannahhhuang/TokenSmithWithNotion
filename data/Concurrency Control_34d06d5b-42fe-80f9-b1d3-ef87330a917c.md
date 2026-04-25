> "A protocol which ensures conflict-serializable schedules. The protocol assures serializability. It can be proved that the transactions can be serialized in the order of their lock points (i.e., the point where a transaction acquired its final lock)."

## **Core Concepts:**

Concurrency control ensures that multiple transactions can execute simultaneously without violating data integrity.

## **Multi-Version Timestamp Ordering (MVTO):**

Unlike standard locking, MVTO maintains multiple physical versions of a single logical data item. When a transaction writes, it creates a new version instead of overwriting the old one. Read operations are then directed to the appropriate version based on the transaction's timestamp, significantly reducing read-write blocking.

## **Two-Phase Locking (2PL):**

Phase 1: Growing Phase. Transaction may obtain locks. Transaction may not release locks.
Phase 2: Shrinking Phase. Transaction may release locks. Transaction may not obtain locks.

Note: Two-phase locking does not ensure freedom from deadlocks. Extensions to basic two-phase locking needed to ensure recoverability of freedom from cascading roll-back.

- **Child Page:** [[Strict vs. Rigorous 2PL]]