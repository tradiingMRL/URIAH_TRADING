## Future Build Direction — Read-Only Monitoring Portal

### Objective
Provide a simple, secure, read-only portal for monitoring system performance, health, and behaviour without exposing any execution or control capability.

### Design Principles
- **Strict separation of concerns**
  - Execution layer (trading engine) is fully isolated from any UI or portal
  - Portal operates in read-only mode against SQLite (no writes, no commands)
- **“Look, no touching” guarantee**
  - No trade execution
  - No parameter changes
  - No system state mutation
- **Single source of truth**
  - Portal reads only from SQLite (post-ingestion data)
  - No direct dependency on live trading processes

### Access & Roles (Planned)
- **Admin (Owner)**
  - Full visibility
  - Diagnostics, gate statistics, early exit analysis
  - System health and exception reporting
- **Viewer (Read-only)**
  - Equity curve
  - Trade list and summaries
  - Daily/weekly performance
  - High-level system status indicators
  - No configuration, no controls

### Security Model
- Password-protected access
- Role-based views
- Portal process runs independently from trading engine
- Failure or misuse of portal cannot impact execution layer

### User Experience Goal
- One-click desktop shortcut or local URL
- Immediate visibility into:
  - Today’s performance
  - System state (healthy / degraded / locked)
  - Trade activity summary
- Suitable for sharing with trusted observers (e.g. family) without operational risk

### Implementation Timing
- **Deferred until after live logging is stable**
- No dependency on this feature for trading correctness
- Enabled by existing logging, schema, and SQLite architecture