# Cyber Patent Catalog

An open, growing catalog of **cybersecurity patents**, harvested from Google Patents across five classification areas, plus working Python code that demonstrates the ideas behind them.

## The data

- **`data/patents.jsonl`** — the full catalog, one patent per line (JSON). Growing automatically: new records are added on a regular schedule.
- **`data/catalog.json`** — the same catalog in a compact single JSON file.

Each record has:

| Field | Meaning |
|---|---|
| `publication_number` | Patent publication number (e.g. US4200770A) |
| `title` | Patent title |
| `abstract_snippet` | Short abstract text |
| `assignee` | Company or organization holding the patent |
| `inventor` | Named inventor(s) |
| `priority_date` / `filing_date` / `grant_date` / `publication_date` | Key dates |
| `language` | Publication language |
| `cpc` | Cooperative Patent Classification code |

### Coverage

| CPC class | Area |
|---|---|
| H04L63 | Network security (firewalls, VPNs, secure protocols) |
| H04L9 | Cryptography |
| G06F21 | System security (access control, malware defense) |
| H04W12 | Wireless network security |
| H04K | Secret communication |

Search by name or description: load `patents.jsonl` in Python and filter on `title`, `abstract_snippet`, `assignee`, or `inventor`.

```python
import json
patents = [json.loads(line) for line in open("data/patents.jsonl")]
firewall = [p for p in patents if "firewall" in p["title"].lower()]
print(len(firewall), "firewall patents")
```

## The code

- **`code/demos/`** — runnable Python demonstrations of landmark patented techniques: Diffie-Hellman key exchange (US 4,200,770), RSA (US 4,405,829), PageRank (US 6,285,999), and a stateful firewall (US 5,606,668).
- **`code/simulators/`** — twelve simulators covering the catalog's categories: block cipher, intrusion detection, VPN tunnel, PKI, access control, malware scanner, DDoS mitigation, Wi-Fi handshake, honeypot, password auth, hash chain, and secure messaging.
- **`code/harvest/`** — the harvester and merge scripts that build this catalog.

## Important note

Patents listed here belong to their respective owners. They are cataloged for **compatibility and certification** — inclusion in this catalog claims no ownership of any third-party patent or product.

## License

Code: MIT. Patent records are public publication data.
