## **External Sort Implementations**

<details><summary>**Basic 2-Way Merge Sort**</summary>
- Pass 0: Read a page, sort it, write it. Only one buffer page is used.
  - Pass 1, 2, ..., N: Merge two runs into one longer run.
</details>

<details><summary>**General External Merge Sort**</summary>
- To sort a file with *N* pages using *B* buffer pages.
  - Pass 0: Read *B* pages at a time, sort internally, produce $\lceil N/B \rceil$ runs of length *B*.
  - Pass 1+: Merge *B-1* runs at a time.
</details>

## **Storage Architectures**

| **Feature** | **Disk-Based Management** | **In-Memory Data Management** |
  |---|---|---|
  | **Primary Bottleneck** | Disk I/O latency | CPU cache misses, memory bandwidth |
  | **Data Structures** | B+ Trees (optimized for block reads) | T-Trees, Cache-conscious B+ Trees |
  | **Recovery** | WAL, heavy logging | Battery-backed RAM, logical logging |
- **Child Page:** [[Advanced Recovery Algorithms]]