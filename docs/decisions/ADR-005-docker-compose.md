# ADR-005: Use Docker Compose for Local Service Orchestration

- **Status:** Accepted
- **Date:** 2026-09-07
- **Scope:** Development and deployment environment

---

## 1. Context

The system contains multiple independently runnable services:

- C++ engine;
- Python analytics;
- Node.js gateway;
- React dashboard.

Each service has different:

- dependencies;
- build systems;
- runtime requirements;
- configuration.

Manually starting every service creates unnecessary operational complexity.

---

## 2. Decision

Docker will be used to containerize each service.

Docker Compose will orchestrate the complete local system.

Architecture:

    docker compose up

          │
          ├── trading-engine
          ├── analytics
          ├── gateway
          └── dashboard

---

## 3. Container Responsibilities

### C++ Engine

Contains:

- compiler/runtime dependencies;
- compiled trading engine;
- engine configuration.

### Python Analytics

Contains:

- Python runtime;
- dependencies;
- analytics application.

### Node Gateway

Contains:

- Node.js runtime;
- production JavaScript/TypeScript build;
- gateway application.

### React Dashboard

Contains:

- frontend build;
- static assets;
- web server.

---

## 4. Network

All services communicate through a private Docker network.

Example:

    trading-network

Service discovery can use Compose service names:

    engine:9000
    analytics:9100
    gateway:8080

The frontend communicates with the gateway rather than directly with internal services.

---

## 5. Environment Configuration

Secrets and environment-specific values must not be hard-coded.

Example:

    .env.example

Configuration includes:

- ports;
- service addresses;
- logging levels;
- simulation speed;
- analytics window sizes.

Actual `.env` files must remain outside version control.

---

## 6. Alternatives Considered

### Manual Processes

Rejected because they are difficult to reproduce.

### Kubernetes

Too complex for the initial development stage.

Kubernetes becomes appropriate when the project requires:

- multiple replicas;
- service discovery;
- autoscaling;
- production orchestration;
- rolling deployments.

### Virtual Machines

Rejected because containers provide a lighter and more developer-friendly environment.

---

## 7. Consequences

### Positive

- Reproducible environment.
- Easy onboarding.
- Consistent dependencies.
- Simple multi-service startup.
- Clear service isolation.

### Negative

- Docker resource overhead.
- More complex debugging.
- Container networking must be understood.
- Build times increase.

---

## 8. Development Workflow

The preferred development workflow is:

    make build
        ↓
    docker compose build
        ↓
    docker compose up
        ↓
    integration tests
        ↓
    dashboard

---

## 9. Future Evolution

If deployment requirements increase, the Compose architecture can become the foundation for Kubernetes manifests or Helm charts.

The service boundaries should remain unchanged during such a migration.