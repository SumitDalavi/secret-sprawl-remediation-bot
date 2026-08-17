# secret-sprawl-remediation-bot Architecture

## System Diagram
The following Mermaid.js sequence diagram maps the core workflow and interactions:

```mermaid
sequenceDiagram
    GitHub->>Bot: Push Event
Bot->>Scanner: Scan commit
Scanner->>Bot: Secret Found
Bot->>GitHub: Revoke & Notify
```

## Component Breakdown
- **Core Technology**: Python, GitHub API
- **Design Paradigm**: Emphasizes high availability, fault tolerance, and security.

## Security & Scaling Considerations
- Strict boundary validations.
- Horizontal scalability achieved via stateless workers.
- Encrypted data at rest and in transit.
