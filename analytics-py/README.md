# Trading Engine Analytics

Python analytics service for the **Trading Engine**.

This component is responsible for consuming market and trade data from the
trading system and calculating technical indicators, portfolio metrics, and
risk metrics.

The service is being developed incrementally. The current implementation
focuses on the Python foundation, domain models, and pure technical-indicator
calculations before integrating them into the streaming analytics pipeline.

---

## Table of Contents

* [Overview](#overview)
* [Responsibilities](#responsibilities)
* [Current Status](#current-status)
* [Architecture](#architecture)
* [Data Flow](#data-flow)
* [Project Structure](#project-structure)
* [Requirements](#requirements)
* [Python Environment](#python-environment)
* [Installation](#installation)
* [Running the Test Suite](#running-the-test-suite)
* [Testing Strategy](#testing-strategy)
* [Domain Models](#domain-models)
* [Technical Indicators](#technical-indicators)

  * [VWAP](#vwap)
  * [SMA](#sma)
  * [EMA](#ema)
  * [Volatility](#volatility)
* [Numeric Precision](#numeric-precision)
* [Input Validation and Error Handling](#input-validation-and-error-handling)
* [Insufficient Historical Data](#insufficient-historical-data)
* [Event Contracts](#event-contracts)
* [Analytics Result](#analytics-result)
* [Configuration](#configuration)
* [Ingestion](#ingestion)
* [Pipeline](#pipeline)
* [Risk Analytics](#risk-analytics)
* [Notebooks](#notebooks)
* [Docker](#docker)
* [Development Workflow](#development-workflow)
* [Performance Considerations](#performance-considerations)
* [Roadmap](#roadmap)
* [Definition of Done](#definition-of-done)
* [Related Documentation](#related-documentation)
* [License](#license)

---

# Overview

`analytics-py` is the Python analytics component of the Trading Engine
platform.

The service is designed to sit downstream of the high-performance C++ trading
engine and provide analytical calculations that can later be consumed by the
gateway and dashboard.

The architecture separates:

```text
Market / Trade Events
        │
        ▼
┌─────────────────────┐
│  Python Ingestion   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Message Parsing     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Analytics Pipeline  │
└──────────┬──────────┘
           │
           ├──────────────► Technical Indicators
           │                 ├── VWAP
           │                 ├── SMA
           │                 ├── EMA
           │                 └── Volatility
           │
           ├──────────────► Portfolio Analytics
           │                 ├── Position
           │                 ├── PnL
           │                 └── Drawdown
           │
           ▼
┌─────────────────────┐
│ Analytics Results   │
└──────────┬──────────┘
           │
           ▼
     Downstream Gateway
```

The implementation currently emphasizes **pure functions, deterministic
calculations, explicit validation, and unit testing**.

---

# Responsibilities

The analytics service is intended to provide the following capabilities:

### Market analytics

* Volume Weighted Average Price (VWAP)
* Simple Moving Average (SMA)
* Exponential Moving Average (EMA)
* Price-return volatility

### Portfolio analytics

* Position tracking
* Realized PnL
* Unrealized PnL
* Equity tracking
* Peak equity
* Drawdown

### Infrastructure

* Market/trade message parsing
* Socket-based ingestion
* Streaming processing
* Analytics result publishing
* Configuration
* Logging
* Time utilities

The components are being implemented incrementally according to the main
Trading Engine roadmap.

---

# Current Status

## Completed

### Phase 3.1 — Python Foundation

The project foundation is established.

Implemented:

* Python package structure
* `pyproject.toml`
* Development dependency configuration
* pytest configuration
* source/test separation
* virtual-environment workflow

### Phase 3.2 — Data Models

Implemented:

* `Tick`
* `Trade`
* `AnalyticsResult`

The models use immutable dataclasses and `Decimal` for price/monetary values.

### Phase 3.3 — Technical Indicators

Implemented:

* VWAP
* SMA
* EMA
* Volatility
* Indicator exports
* Unit tests
* Input validation
* Insufficient-data handling

Current test suite:

```text
55 tests
55 passed
```

## In Progress / Planned

The following modules exist in the project structure but are not yet considered
complete:

* ingestion integration
* streaming processor integration
* publisher integration
* position calculation
* PnL calculation
* drawdown calculation
* risk manager integration
* production configuration
* end-to-end analytics streaming

These will be implemented in later phases.

---

# Architecture

The Python service follows a layered structure.

```text
analytics-py/
│
├── config/
│       Application configuration
│
├── indicators/
│       Stateless technical calculations
│
├── ingestion/
│       Input/event handling
│
├── models/
│       Domain objects
│
├── pipeline/
│       Streaming analytics orchestration
│
├── risk/
│       Portfolio and risk calculations
│
└── utils/
        Shared utilities
```

The core calculation layer is intentionally kept independent from networking
and infrastructure.

For example:

```text
Network Event
     │
     ▼
Parser
     │
     ▼
Domain Model
     │
     ▼
Pure Calculation
     │
     ▼
Analytics Result
```

This makes calculations easier to test and reason about independently.

---

# Data Flow

The intended data flow is:

```text
C++ Trading Engine
        │
        │ Trade / Market Events
        ▼
Python Analytics
        │
        ├── Parse event
        │
        ├── Validate event
        │
        ├── Convert to domain model
        │
        ├── Update analytical state
        │
        ├── Calculate indicators
        │
        └── Produce analytics update
        │
        ▼
Node Gateway
        │
        ▼
React Dashboard
```

The C++ engine remains responsible for high-performance matching and order-book
processing.

The Python service is responsible for analytical processing rather than order
matching.

---

# Project Structure

```text
analytics-py/
│
├── notebooks/
│   ├── strategy-analysis.ipynb
│   └── vwap-analysis.ipynb
│
├── src/
│   └── analytics/
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       │
│       ├── indicators/
│       │   ├── __init__.py
│       │   ├── ema.py
│       │   ├── sma.py
│       │   ├── volatility.py
│       │   └── vwap.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── message_parser.py
│       │   └── socket_client.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── analytics_result.py
│       │   ├── tick.py
│       │   └── trade.py
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── processor.py
│       │   └── publisher.py
│       │
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── drawdown.py
│       │   ├── pnl.py
│       │   ├── position_sizing.py
│       │   └── risk_manager.py
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   └── time.py
│       │
│       ├── __init__.py
│       └── main.py
│
├── tests/
│   ├── fixtures/
│   │   ├── expected_metrics.json
│   │   └── ticks.json
│   │
│   ├── integration/
│   │   └── test_pipeline.py
│   │
│   └── unit/
│       ├── test_ema.py
│       ├── test_sma.py
│       ├── test_volatility.py
│       ├── test_vwap.py
│       ├── test_models.py
│       ├── test_pnl.py
│       └── test_drawdown.py
│
├── Dockerfile
├── README.md
├── pyproject.toml
└── requirements.txt
```

Some directories contain scaffolding for later implementation phases.

---

# Requirements

The project requires:

* Python 3.11 or newer
* `pip`
* `venv`

Development/testing dependencies:

* pytest
* pytest-cov

The current development environment has been tested with:

```text
Python 3.14.7
pytest 9.1.1
pytest-cov 7.1.0
coverage 7.16.0
```

---

# Python Environment

A project-local virtual environment is recommended.

Create it:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Verify:

```bash
python --version
which python
```

The Python executable should resolve to the project's `.venv`.

---

# Installation

From the `analytics-py` directory:

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip
```

Install the project with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Verify the installation:

```bash
python -c "import analytics; print(analytics.__file__)"
```

---

# Running the Test Suite

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run coverage:

```bash
pytest --cov=src/analytics --cov-report=term-missing
```

Run only indicator tests:

```bash
pytest tests/unit/test_vwap.py \
       tests/unit/test_sma.py \
       tests/unit/test_ema.py \
       tests/unit/test_volatility.py
```

Run an individual indicator:

```bash
pytest tests/unit/test_vwap.py -v
```

---

# Testing Strategy

The analytics project follows a layered testing strategy.

## Unit Tests

Pure calculations are tested independently.

Current indicator coverage includes:

```text
VWAP
SMA
EMA
Volatility
```

Tests cover:

* normal calculations
* hand-calculated expected values
* single observations
* moving windows
* insufficient data
* invalid periods
* empty input
* invalid quantities
* invalid prices
* EMA recursive calculations
* volatility edge cases

## Domain Model Tests

Domain models are tested for:

* valid construction
* required fields
* invalid values
* event type validation
* serialization
* Decimal conversion
* timestamp serialization

## Integration Tests

The project contains an integration-test structure for the future streaming
pipeline.

As the ingestion and processor layers become fully implemented, integration
tests will validate the complete event-to-result flow.

---

# Domain Models

The core domain models are implemented using Python dataclasses.

They are immutable and use slots.

```python
@dataclass(frozen=True, slots=True)
```

This prevents accidental modification of domain events after construction.

---

## Tick

`Tick` represents a market price/quantity observation.

Fields:

```text
event_id
event_type
symbol
price
quantity
timestamp
```

Example:

```json
{
  "event_id": "evt-000200",
  "event_type": "MARKET_TICK",
  "symbol": "SIM",
  "price": "101.20",
  "quantity": 15,
  "timestamp": "2026-09-07T12:00:02+00:00"
}
```

Validation includes:

* non-empty event ID
* correct event type
* non-empty symbol
* positive price
* positive quantity

---

# Trade

`Trade` represents an authoritative executed trade.

Fields:

```text
event_id
event_type
trade_id
symbol
price
quantity
timestamp
buy_order_id
sell_order_id
```

Example:

```json
{
  "event_id": "evt-000201",
  "event_type": "TRADE",
  "trade_id": "trade-001",
  "symbol": "SIM",
  "price": "101.20",
  "quantity": 15,
  "timestamp": "2026-09-07T12:00:02+00:00",
  "buy_order_id": "order-buy-001",
  "sell_order_id": "order-sell-001"
}
```

---

# AnalyticsResult

`AnalyticsResult` represents calculated analytics intended for downstream
consumers.

Fields include:

```text
event_id
event_type
symbol
price
vwap
sma
ema
position
realized_pnl
unrealized_pnl
equity
peak_equity
drawdown
timestamp
```

The model validates:

* event ID
* event type
* symbol
* positive price
* peak equity >= equity
* non-negative drawdown

---

# Technical Indicators

The current indicator layer contains pure functions.

```text
analytics.indicators
│
├── calculate_vwap(...)
├── calculate_sma(...)
├── calculate_ema(...)
└── calculate_volatility(...)
```

The functions do not depend on networking, sockets, databases, or the
streaming pipeline.

---

# VWAP

## Definition

Volume Weighted Average Price calculates the average price weighted by traded
quantity.

```text
VWAP = sum(price × quantity) / sum(quantity)
```

Where:

```text
price     = observed trade price
quantity  = corresponding traded volume
```

## Example

```python
from decimal import Decimal

from analytics.indicators import calculate_vwap

prices = [
    Decimal("100.00"),
    Decimal("101.00"),
    Decimal("102.00"),
]

quantities = [10, 20, 30]

result = calculate_vwap(prices, quantities)
```

Calculation:

```text
(100 × 10 + 101 × 20 + 102 × 30) / 60

= 6080 / 60

= 101.333333...
```

## Validation

VWAP rejects:

* empty input
* mismatched price/quantity lengths
* zero quantities
* negative quantities

The implementation uses `Decimal` arithmetic.

---

# SMA

## Definition

Simple Moving Average calculates the arithmetic mean of the latest `N`
observations.

```text
SMA = sum(last N prices) / N
```

Example:

```python
from decimal import Decimal

from analytics.indicators import calculate_sma

prices = [
    Decimal("100.00"),
    Decimal("101.00"),
    Decimal("102.00"),
    Decimal("103.00"),
    Decimal("104.00"),
]

result = calculate_sma(prices, 3)
```

The latest three observations are used:

```text
(102 + 103 + 104) / 3

= 103
```

## Window Semantics

The pure function receives the available price history and uses only the latest
`period` observations.

If:

```text
len(prices) < period
```

the function returns:

```python
None
```

The future streaming processor can maintain a bounded rolling window rather
than repeatedly storing the complete market history.

---

# EMA

## Definition

Exponential Moving Average gives greater weight to recent observations.

```text
EMA_t = alpha × price_t + (1 - alpha) × EMA_(t-1)
```

The smoothing factor is:

```text
alpha = 2 / (N + 1)
```

---

## EMA Initialization

The implementation initializes the first EMA using the SMA of the first
`period` observations.

For:

```text
period = 3
```

and:

```text
100
101
102
```

the initial EMA is:

```text
(100 + 101 + 102) / 3
= 101
```

Then:

```text
alpha = 2 / (3 + 1)
      = 0.5
```

For the next price `103`:

```text
EMA = 0.5 × 103 + 0.5 × 101
    = 102
```

This initialization rule is explicitly implemented and tested.

---

## EMA Behavior

The implementation:

* validates that `period` is positive;
* rejects empty input;
* returns `None` when insufficient observations exist;
* initializes EMA with SMA;
* recursively processes subsequent prices.

---

# Volatility

## Definition

The current implementation defines volatility as the **sample standard
deviation of simple price returns**.

A simple return is:

```text
return = (current_price - previous_price) / previous_price
```

For a volatility period `N`, the latest `N` returns are used.

The sample variance is:

```text
variance =
    sum((return - mean_return)^2) / (N - 1)
```

Volatility is:

```text
volatility = sqrt(variance)
```

---

## Observation Requirement

A period of `N` returns requires:

```text
N + 1
```

price observations.

For example:

```text
period = 3
```

requires at least:

```text
4 prices
```

because:

```text
P1 → P2
P2 → P3
P3 → P4
```

produce three returns.

---

## Example

```python
from decimal import Decimal

from analytics.indicators import calculate_volatility

prices = [
    Decimal("100.00"),
    Decimal("102.00"),
    Decimal("101.00"),
    Decimal("104.00"),
]

result = calculate_volatility(prices, 3)
```

The function calculates the three latest simple returns and returns their
sample standard deviation.

---

## Volatility Validation

The implementation rejects:

* empty prices;
* non-positive periods;
* zero prices;
* negative prices.

If there are not enough observations, it returns `None`.

For a single return (`period=1`), the standard deviation is defined by the
implementation as:

```text
0
```

because one observation has no measurable dispersion.

---

# Numeric Precision

Financial calculations require careful handling of numeric values.

The analytics core uses:

```python
Decimal
```

instead of binary floating-point values for prices and monetary calculations.

Example:

```python
from decimal import Decimal

price = Decimal("101.20")
```

This is especially important for:

* price calculations;
* VWAP;
* SMA;
* EMA;
* PnL;
* equity;
* drawdown.

The indicator implementations do not force a global decimal precision.
Arithmetic follows Python's active `Decimal` context.

The project intentionally avoids adding NumPy/Pandas to the core calculation
layer at this stage.

The goal is to keep the initial analytics engine:

* deterministic;
* dependency-light;
* explicit;
* easy to test;
* suitable for financial arithmetic.

Vectorized numerical libraries can be evaluated later if profiling demonstrates
a need for them.

---

# Input Validation and Error Handling

Invalid input should fail explicitly instead of producing misleading
analytics.

Examples include:

```text
period <= 0
empty price collection
non-positive prices
non-positive quantities
mismatched VWAP inputs
invalid domain-event types
```

These cases generally raise:

```python
ValueError
```

Example:

```python
calculate_sma([], 3)
```

raises a `ValueError`.

---

# Insufficient Historical Data

Insufficient historical data is not considered invalid input.

For valid input where the requested calculation cannot yet be produced, the
indicator returns:

```python
None
```

For example:

```python
calculate_sma(
    [
        Decimal("100.00"),
        Decimal("101.00"),
    ],
    3,
)
```

returns:

```python
None
```

Similarly, volatility with period `3` requires four prices.

This distinction is important:

```text
Invalid input
     │
     └──► ValueError

Valid input + insufficient history
     │
     └──► None

Valid input + sufficient history
     │
     └──► Decimal result
```

---

# Event Contracts

The analytics service uses the event model defined by the overall Trading
Engine architecture.

External events contain common fields such as:

```text
event_id
event_type
timestamp
```

Market tick example:

```json
{
  "event_type": "MARKET_TICK",
  "event_id": "evt-000200",
  "symbol": "SIM",
  "price": 101.20,
  "quantity": 15,
  "timestamp": "2026-09-07T12:00:02.000Z"
}
```

Trade events represent authoritative executions and are expected to be the
primary source for downstream trade analytics.

---

# Analytics Result

The intended output event type is:

```text
ANALYTICS_UPDATE
```

Example:

```json
{
  "event_type": "ANALYTICS_UPDATE",
  "event_id": "evt-000201",
  "symbol": "SIM",
  "price": 101.20,
  "vwap": 101.13,
  "sma": 101.10,
  "ema": 101.16,
  "position": 150,
  "realized_pnl": 120.00,
  "unrealized_pnl": 64.50,
  "equity": 10184.50,
  "peak_equity": 10210.00,
  "drawdown": 25.50,
  "timestamp": "2026-09-07T12:00:02.000Z"
}
```

The `AnalyticsResult` domain model already represents this contract.

The full streaming production flow will be completed in later implementation
phases.

---

# Configuration

Configuration code is located under:

```text
src/analytics/config/
```

Current structure:

```text
config/
├── __init__.py
└── settings.py
```

Configuration is intentionally separated from calculation logic.

Future configuration will cover items such as:

* analytics service settings;
* engine connection;
* gateway connection;
* indicator periods;
* logging;
* runtime behavior.

---

# Ingestion

The ingestion layer is located under:

```text
src/analytics/ingestion/
```

Current structure:

```text
ingestion/
├── __init__.py
├── message_parser.py
└── socket_client.py
```

Its intended responsibilities are:

```text
Network/Event Input
       │
       ▼
Message Parser
       │
       ▼
Validated Domain Event
```

The ingestion layer will remain separate from the indicator calculations.

This allows indicators to remain pure and independently testable.

---

# Pipeline

The pipeline layer is located under:

```text
src/analytics/pipeline/
```

Current structure:

```text
pipeline/
├── __init__.py
├── processor.py
└── publisher.py
```

The intended processing flow is:

```text
Incoming Event
      │
      ▼
Parse
      │
      ▼
Validate
      │
      ▼
Update Analytics State
      │
      ├── VWAP
      ├── SMA
      ├── EMA
      ├── Volatility
      ├── Position
      ├── PnL
      └── Drawdown
      │
      ▼
AnalyticsResult
      │
      ▼
Publisher
```

Streaming integration is intentionally separated from the currently completed
pure indicator functions.

---

# Risk Analytics

The risk layer is located under:

```text
src/analytics/risk/
```

Current structure:

```text
risk/
├── __init__.py
├── drawdown.py
├── pnl.py
├── position_sizing.py
└── risk_manager.py
```

The intended responsibilities include:

### Position

Track the net position:

```text
position =
    cumulative_buy_quantity
    -
    cumulative_sell_quantity
```

### PnL

Calculate:

* realized PnL;
* unrealized PnL;
* equity.

### Drawdown

Track:

```text
peak equity
current equity
drawdown
```

### Position sizing

Provide future risk-aware position-sizing functionality.

### Risk manager

Coordinate risk calculations and constraints.

These modules are part of the planned analytics architecture but are not
currently treated as complete simply because their files exist.

---

# Notebooks

The project includes notebooks for exploratory analytics:

```text
notebooks/
├── strategy-analysis.ipynb
└── vwap-analysis.ipynb
```

These notebooks are intended for:

* experimentation;
* visualization;
* strategy analysis;
* validating analytical assumptions;
* exploring market data.

Production calculations should remain in the tested Python modules under
`src/analytics`.

---

# Docker

A Dockerfile is included:

```text
Dockerfile
```

The purpose of the container image is to provide a reproducible runtime for
the analytics service.

Containerization will become more important as the analytics service is
integrated with:

```text
C++ Engine
    │
    ▼
Python Analytics
    │
    ▼
Node Gateway
    │
    ▼
React Dashboard
```

The final production container workflow will be aligned with the project's
overall Docker phase.

---

# Development Workflow

Work from the `analytics-py` directory.

Activate the environment:

```bash
source .venv/bin/activate
```

Run tests:

```bash
pytest
```

Check formatting/status:

```bash
git status
```

Inspect changes:

```bash
git diff
```

Check the summary:

```bash
git diff --stat
```

Before completing a development step:

```bash
pytest
git status
git diff --stat
```

Generated virtual-environment files must not be committed.

The `.gitignore` contains:

```text
.venv/
```

---

# Development Principles

The analytics service follows several implementation principles.

## 1. Pure calculations first

Indicator calculations are implemented as pure functions before streaming
integration.

For example:

```text
calculate_vwap(...)
calculate_sma(...)
calculate_ema(...)
calculate_volatility(...)
```

This allows mathematical behavior to be tested independently.

---

## 2. Explicit financial arithmetic

Use:

```python
Decimal
```

for prices and monetary values.

---

## 3. Explicit validation

Invalid inputs should produce clear exceptions.

---

## 4. Deterministic behavior

The same input should produce the same output.

This makes unit testing and debugging easier.

---

## 5. Separation of concerns

The project separates:

```text
Models
Indicators
Ingestion
Pipeline
Risk
Configuration
Utilities
```

Networking should not be mixed into mathematical calculation functions.

---

## 6. Test before integration

A calculation should first have deterministic unit tests before being
connected to the streaming pipeline.

---

# Performance Considerations

The current implementation prioritizes correctness and maintainability.

The core indicator functions intentionally use straightforward Python and
`Decimal` arithmetic.

For example, the current pure functions may convert incoming iterables to
lists so they can validate and access the required observations.

This is appropriate for the initial implementation and testing stage.

For a production high-throughput stream, the pipeline can later maintain
bounded rolling state such as:

```text
SMA
 └── rolling queue + running sum

VWAP
 └── cumulative/windowed price-volume state

EMA
 └── previous EMA + latest price

Volatility
 └── rolling return window/statistics
```

Performance optimization should be driven by benchmarks rather than introduced
prematurely.

The high-performance matching path remains implemented in C++.

---

# Roadmap

The Python analytics service follows the overall Trading Engine roadmap.

## Phase 3.1 — Python Foundation

Status:

```text
Complete
```

Objectives:

* establish package structure;
* configure Python project;
* configure tests;
* establish reproducible development environment.

---

## Phase 3.2 — Data Models

Status:

```text
Complete
```

Implemented:

```text
Tick
Trade
AnalyticsResult
```

---

## Phase 3.3 — Technical Indicators

Status:

```text
In Progress
```

Implementation order:

```text
3.3.1  VWAP
3.3.2  SMA
3.3.3  EMA
3.3.4  Volatility
3.3.5  Indicator unit tests
```

Current status:

```text
VWAP          Complete
SMA           Complete
EMA           Complete
Volatility    Complete
Unit tests    Complete
```

Current test result:

```text
55 passed
```

---

## Future Analytics Work

Planned:

```text
Position
PnL
Drawdown
Position sizing
Risk manager
Streaming processor
Message ingestion
Publisher
Integration tests
```

---

# Definition of Done

An analytics component is considered complete when it has:

* implementation;
* unit tests;
* validation;
* appropriate error handling;
* useful documentation;
* reproducible installation;
* deterministic test behavior;
* integration coverage where applicable;
* demonstrated expected behavior.

For mathematical calculations, hand-calculated fixtures should match automated
results.

---

# Current Test Baseline

At the current Phase 3.3 indicator stage:

```text
============================= test session =============================

55 tests collected

55 passed

============================== 0 failures ==============================
```

The test suite covers the currently implemented domain models and technical
indicators.

---

# Related Documentation

The broader Trading Engine documentation is located in the repository's
`docs/` directory.

Important documents include:

```text
docs/
├── 03-data-model.md
├── 05-roadmap-and-phases.md
├── 15-performance-benchmarks.md
├── 16-contributing.md
├── 17-changelog.md
└── adr/
```

In particular:

### Data Model

```text
docs/03-data-model.md
```

Defines the event contracts and analytical data model shared by the platform.

### Roadmap

```text
docs/05-roadmap-and-phases.md
```

Defines the implementation phases and exit criteria for the Python analytics
service.

---

# Relationship With the Trading Engine

The complete platform is organized approximately as:

```text
┌──────────────────────────────────────────────────────────┐
│                    Trading Platform                      │
│                                                          │
│  ┌──────────────┐                                        │
│  │ C++ Engine   │                                        │
│  │              │                                        │
│  │ Order Book   │                                        │
│  │ Matching     │                                        │
│  │ Transport    │                                        │
│  └──────┬───────┘                                        │
│         │                                                │
│         │ Events                                         │
│         ▼                                                │
│  ┌────────────────────┐                                  │
│  │ Python Analytics   │                                  │
│  │                    │                                  │
│  │ Indicators         │                                  │
│  │ Position           │                                  │
│  │ PnL                │                                  │
│  │ Risk               │                                  │
│  └─────────┬──────────┘                                  │
│            │                                             │
│            ▼                                             │
│  ┌────────────────────┐                                  │
│  │ Node Gateway       │                                  │
│  │ REST / WebSocket   │                                  │
│  └─────────┬──────────┘                                  │
│            │                                             │
│            ▼                                             │
│  ┌────────────────────┐                                  │
│  │ React Dashboard    │                                  │
│  └────────────────────┘                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

The Python service therefore acts as the analytical layer between the trading
engine and the application-facing gateway.

---

# License

This project is currently developed as a portfolio and engineering project.

License information will be added according to the licensing decision for the
overall Trading Engine repository.
