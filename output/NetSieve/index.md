# Tutorial: NetSieve

NetSieve acts as a local *DNS filter*. It receives DNS requests from devices on your network.
If a requested domain (like `ads.example.com`) is found in its *blocklists*, NetSieve prevents access by replying with `0.0.0.0`.
Otherwise, it checks for *local overrides* or forwards the request to a public **upstream DNS server** (like Cloudflare or Google) to get the real IP address.
The blocklists are automatically downloaded and updated from online sources defined in the **configuration**.


**Source Repository:** [https://github.com/krishnadeepy/NetSieve](https://github.com/krishnadeepy/NetSieve)

```mermaid
flowchart TD
    A0["Blocklist Data Management"]
    A1["DNS Server Framework"]
    A2["DNS Query Resolution"]
    A3["Database ORM (HostEntry)"]
    A4["System Configuration"]
    A5["Upstream DNS Forwarding"]
    A6["Local DNS Records"]
    A0 -- "Stores fetched data using" --> A3
    A0 -- "Reads blocklist URLs from" --> A4
    A1 -- "Delegates requests to" --> A2
    A1 -- "Reads server port from" --> A4
    A2 -- "Checks block status via" --> A3
    A2 -- "Uses for external lookups" --> A5
    A2 -- "Checks for local overrides" --> A6
    A3 -- "Reads DB config from" --> A4
    A5 -- "Reads upstream servers from" --> A4
    A6 -- "Is defined in" --> A4
```

## Chapters

1. [System Configuration](01_system_configuration.md)
2. [DNS Server Framework](02_dns_server_framework.md)
3. [DNS Query Resolution](03_dns_query_resolution.md)
4. [Blocklist Data Management](04_blocklist_data_management.md)
5. [Local DNS Records](05_local_dns_records.md)
6. [Upstream DNS Forwarding](06_upstream_dns_forwarding.md)
7. [Database ORM (HostEntry)](07_database_orm__hostentry_.md)
