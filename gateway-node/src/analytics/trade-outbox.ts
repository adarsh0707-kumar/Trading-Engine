import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

import { Database } from "bun:sqlite";

export interface TradeOutboxRecord {
  readonly eventId: string;
  readonly message: Buffer;
}

export interface TradeOutbox {
  readonly enqueue: (eventId: string, message: Buffer) => void;
  readonly listPending: () => readonly TradeOutboxRecord[];
  readonly acknowledge: (eventId: string) => void;
  readonly close: () => void;
}

/**
 * SQLite-backed outbox for analytics trade delivery.
 *
 * FULL synchronous commits make an enqueue durable before sendTrade reports
 * success. Rows are removed only after analytics confirms database persistence.
 */
export class SqliteTradeOutbox implements TradeOutbox {
  private readonly database: Database;

  public constructor(path: string) {
    if (path.trim().length === 0) {
      throw new Error("Trade outbox path must not be empty");
    }

    mkdirSync(dirname(path), { recursive: true });
    this.database = new Database(path, { create: true });
    this.database.exec("PRAGMA journal_mode = WAL");
    this.database.exec("PRAGMA synchronous = FULL");
    this.database.exec(`
      CREATE TABLE IF NOT EXISTS analytics_trade_outbox (
        event_id TEXT PRIMARY KEY NOT NULL,
        framed_message TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  public enqueue(eventId: string, message: Buffer): void {
    if (eventId.trim().length === 0) {
      throw new Error("Trade outbox event ID must not be empty");
    }

    const encoded = message.toString("base64");
    const existing = this.database
      .query<{ framed_message: string }, [string]>(
        "SELECT framed_message FROM analytics_trade_outbox WHERE event_id = ?",
      )
      .get(eventId);

    if (existing !== null && existing !== undefined) {
      if (existing.framed_message !== encoded) {
        throw new Error(`Trade outbox event ID collision: ${eventId}`);
      }
      return;
    }

    this.database
      .query(
        "INSERT INTO analytics_trade_outbox (event_id, framed_message) VALUES (?, ?)",
      )
      .run(eventId, encoded);
  }

  public listPending(): readonly TradeOutboxRecord[] {
    const rows = this.database
      .query<{ event_id: string; framed_message: string }, []>(
        "SELECT event_id, framed_message FROM analytics_trade_outbox ORDER BY rowid",
      )
      .all();

    return rows.map((row) => ({
      eventId: row.event_id,
      message: Buffer.from(row.framed_message, "base64"),
    }));
  }

  public acknowledge(eventId: string): void {
    this.database
      .query("DELETE FROM analytics_trade_outbox WHERE event_id = ?")
      .run(eventId);
  }

  public close(): void {
    this.database.close();
  }
}
