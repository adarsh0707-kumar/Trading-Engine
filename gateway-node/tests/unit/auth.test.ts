import { describe, expect, test } from "bun:test";

import {
  anonymousAuthentication,
  hasAuthorization,
  requireAuthentication,
  requireAuthorization,
} from "../../src/security/auth.ts";

describe("authentication and authorization boundary", () => {
  test("represents an unauthenticated request explicitly", () => {
    expect(anonymousAuthentication()).toEqual({ authenticated: false });
    expect(() => requireAuthentication(anonymousAuthentication())).toThrow(
      "Authentication required",
    );
  });

  test("returns the principal for authenticated requests", () => {
    const principal = {
      subject: "user-123",
      roles: ["trader"],
      scopes: ["market:read", "orders:write"],
    } as const;

    expect(
      requireAuthentication({
        authenticated: true,
        principal,
      }),
    ).toEqual(principal);
  });

  test("authorizes matching roles and scopes", () => {
    const principal = {
      subject: "user-123",
      roles: ["trader"],
      scopes: ["market:read", "orders:write"],
    } as const;

    expect(() =>
      requireAuthorization(principal, {
        roles: ["trader"],
        scopes: ["market:read"],
      }),
    ).not.toThrow();

    expect(hasAuthorization(principal, { roles: ["admin"] })).toBe(false);
    expect(hasAuthorization(principal, { scopes: ["market:write"] })).toBe(false);
  });

  test("requires every requested scope", () => {
    const principal = {
      subject: "user-123",
      roles: ["trader"],
      scopes: ["market:read"],
    } as const;

    expect(() =>
      requireAuthorization(principal, { scopes: ["market:read", "orders:write"] }),
    ).toThrow("Access denied");
  });
});
