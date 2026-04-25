> 💡 **Callout:** **Key Insight:** Recovery algorithms must handle both transaction failure (aborts) and system crashes (power loss).

## **The ARIES Protocol**

ARIES is a state-of-the-art recovery algorithm based on the Write-Ahead Logging (WAL) protocol. It requires tracking the **Log Sequence Number (LSN)** for every operation.

Three Main Passes of ARIES:

- **Analysis:** Determines the point of failure and identifies dirty pages in the buffer pool.
- **Redo:** Repeats *all* actions starting from the smallest `recLSN` to restore the database state to exactly what it was at the time of the crash.
- **Undo:** Reverses the actions of transactions that did not commit before the crash, going backward through the log.
Log Record JSON Structure

```json
{
  "log_record": {
    "lsn": 1048576,
    "prev_lsn": 1048500,
    "transaction_id": "T_9942",
    "type": "UPDATE",
    "page_id": "P_409",
    "undo_next_lsn": null
  }
}
```