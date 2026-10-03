import { afterEach, describe, expect, test } from "bun:test";
import Fastify, { type FastifyInstance } from "fastify";

import {
  conflict,
  dependencyUnavailable,
  forbidden,
  internalError,
  invalidArgument,
  notFound,
  unauthorized,
} from "../src/errors/api-error.ts";
import { registerErrorHandler } from "../src/errors/error-handler.ts";

const apps: FastifyInstance[] = [];

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()));
});

function createTestApp() {
  const app = Fastify({ logger: false });
  registerErrorHandler(app);
  apps.push(app);
  return app;
}

describe("public API error contract", () => {
  test("sanitizes internal ApiError messages for every public error code", async () => {
    const cases = [
      [400, invalidArgument("database password=secret"), "INVALID_ARGUMENT", "Request validation failed"],
      [401, unauthorized("authorization token=secret"), "UNAUTHORIZED", "Authentication required"],
      [403, forbidden("admin policy=secret"), "FORBIDDEN", "Access denied"],
      [404, notFound("internal table=secret"), "NOT_FOUND", "Resource not found"],
      [409, conflict("state details=secret"), "CONFLICT", "Request conflicts with the current state"],
      [503, dependencyUnavailable("postgres host=secret"), "DEPENDENCY_UNAVAILABLE", "Required dependency is unavailable"],
      [500, internalError("stack trace=secret"), "INTERNAL_ERROR", "Internal server error"],
    ] as const;

    for (const [status, error, code, message] of cases) {
      const app = createTestApp();

      app.get("/error", async () => {
        throw error;
      });

      const response = await app.inject({
        method: "GET",
        url: "/error",
      });

      expect(response.statusCode).toBe(status);
      expect(response.json()).toMatchObject({
        error: {
          code,
          message,
          request_id: expect.any(String),
        },
      });
      expect(response.body).not.toContain("secret");
    }
  });

  test("returns the stable public contract for unexpected errors", async () => {
    const app = createTestApp();

    app.get("/error", async () => {
      throw new Error("database password=secret stack=secret");
    });

    const response = await app.inject({
      method: "GET",
      url: "/error",
    });

    expect(response.statusCode).toBe(500);
    expect(response.json()).toMatchObject({
      error: {
        code: "INTERNAL_ERROR",
        message: "Internal server error",
        request_id: expect.any(String),
      },
    });
    expect(response.body).not.toContain("secret");
  });

  test("returns a stable 404 message without framework internals", async () => {
    const app = createTestApp();

    const response = await app.inject({
      method: "GET",
      url: "/does-not-exist",
    });

    expect(response.statusCode).toBe(404);
    expect(response.json()).toMatchObject({
      error: {
        code: "NOT_FOUND",
        message: "Route not found",
        request_id: expect.any(String),
      },
    });
  });
});
