import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, test } from "bun:test";

import { SqliteTradeOutbox } from "../src/analytics/trade-outbox.ts";

const temporaryDirectories: string[] = [];

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    rmSync(directory, { recursive: true, force: true });
  }
});

function createOutboxPath(): string {
  const directory = mkdtempSync(join(tmpdir(), "gateway-trade-outbox-"));
  temporaryDirectories.push(directory);
  return join(directory, "outbox.sqlite");
}

describe("SQLite trade outbox", () => {
  test("recovers pending deliveries after reopening the database", () => {
    const path = createOutboxPath();
    const message = Buffer.from([0, 0, 0, 2, 123, 125]);

    const first = new SqliteTradeOutbox(path);
    first.enqueue("trade-1", message);
    first.close();

    const reopened = new SqliteTradeOutbox(path);
    try {
      expect(reopened.listPending()).toEqual([
        { eventId: "trade-1", message },
      ]);
    } finally {
      reopened.close();
    }
  });

  test("acknowledges a trade by removing its durable pending row", () => {
    const outbox = new SqliteTradeOutbox(createOutboxPath());
    try {
      outbox.enqueue("trade-1", Buffer.from("framed-message"));
      outbox.acknowledge("trade-1");
      expect(outbox.listPending()).toEqual([]);
    } finally {
      outbox.close();
    }
  });

  test("accepts an identical duplicate enqueue but rejects event ID collisions", () => {
    const outbox = new SqliteTradeOutbox(createOutboxPath());
    try {
      outbox.enqueue("trade-1", Buffer.from("first"));
      expect(() => outbox.enqueue("trade-1", Buffer.from("first"))).not.toThrow();
      expect(() => outbox.enqueue("trade-1", Buffer.from("different"))).toThrow(
        "Trade outbox event ID collision: trade-1",
      );
      expect(outbox.listPending()).toHaveLength(1);
    } finally {
      outbox.close();
    }
  });
});
