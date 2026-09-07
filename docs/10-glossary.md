# Glossary

## A

### API
Application Programming Interface. A defined way for software components to communicate.

### Ask
The lowest price at which a sell order is currently available.

### Analytics
Calculations performed on market/trade data, such as VWAP, moving averages, and PnL.

### Atomic operation
An operation that can be observed as indivisible for synchronization purposes.

---

## B

### Backpressure
A mechanism used when a producer is faster than a consumer. The system must slow, buffer, batch, or otherwise control the flow.

### Bid
The highest price currently offered by a buyer.

### Book
Short for order book.

---

## C

### C++ Engine
The performance-oriented service responsible for simulated orders, order-book state, and matching.

### Correlation ID
An identifier used to trace one request/event across multiple services.

### Container
An isolated runtime package containing application code and its dependencies.

---

## D

### Dashboard
The React browser interface displaying live simulation data.

### Drawdown
The reduction from a historical peak equity value to a current lower value.

### Docker Compose
A tool for defining and running multiple containers as one application.

---

## E

### EMA
Exponential Moving Average. A moving average that gives greater weight to recent observations.

### Event
A record describing something that happened in the system.

### Event-driven architecture
An architecture where components communicate by producing and consuming events.

---

## F

### Fill
The execution of some or all of an order.

### FIFO
First In, First Out. Used for time priority among orders at the same price.

---

## G

### Gateway
The Node.js service between the browser and internal services.

### gRPC
A remote procedure call framework commonly paired with Protocol Buffers.

---

## H

### Health check
An endpoint or probe indicating whether a service is operating correctly.

---

## I

### IPC
Inter-Process Communication. Techniques for processes to exchange information, such as sockets or shared memory.

### Instrument
A tradable simulated asset, such as the project's `SIM` symbol.

---

## L

### Limit order
An order with a maximum buy price or minimum sell price.

### Latency
Time taken for an event or operation to travel from one point to another.

### Low latency
An engineering objective of reducing processing and communication delay.

---

## M

### Market data
Information describing simulated market activity.

### Market order
An order intended to execute immediately at available prices. Optional for the MVP.

### Matching engine
The component that determines which compatible buy and sell orders trade.

### Moving average
An indicator calculated from a rolling set of observations.

---

## N

### Node.js
JavaScript runtime used here for the API gateway and WebSocket layer.

### NDJSON
Newline-delimited JSON. Each line contains one JSON object.

---

## O

### Order
An instruction to buy or sell a simulated instrument.

### Order book
A collection of active buy and sell orders organized by price and time.

### Order ID
Unique identifier assigned to an order.

---

## P

### Partial fill
An order execution where only part of the requested quantity is matched.

### PnL
Profit and Loss.

### Price-time priority
Matching rule where the best price has priority, followed by earlier arrival time at the same price.

### Protocol Buffer
A schema-based binary serialization format often used with gRPC.

---

## Q

### Quantity
Number of units associated with an order or trade.

---

## R

### React
Frontend library used to build the trading dashboard.

### REST
HTTP request/response API style used for non-streaming operations.

### Risk metric
A measurement describing exposure, drawdown, or related portfolio characteristics.

---

## S

### SMA
Simple Moving Average.

### Socket
An endpoint used for process/network communication.

### Spread
Difference between best ask and best bid.

### Shared memory
An IPC mechanism where processes access a common memory region.

### Simulation
A controlled model of market behavior that does not execute real transactions.

---

## T

### Tick
A simulated market data observation.

### Trade
A completed match between compatible buy and sell orders.

### Throughput
Number of events or operations processed per unit of time.

---

## V

### VWAP
Volume-Weighted Average Price:

\[
VWAP = \frac{\sum(P_iQ_i)}{\sum Q_i}
\]

---

## W

### WebSocket
A persistent, bidirectional communication channel commonly used for real-time browser updates.

---

## Z

### Zero-copy
A design objective in which data is transferred without unnecessary memory copying. Shared-memory IPC can reduce copies but introduces synchronization complexity.
