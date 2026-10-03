import { forbidden, unauthorized } from "../errors/api-error.ts";

export type AuthenticatedPrincipal = Readonly<{
  subject: string;
  roles: readonly string[];
  scopes: readonly string[];
}>;

export type AuthenticationState =
  | Readonly<{ authenticated: false }>
  | Readonly<{ authenticated: true; principal: AuthenticatedPrincipal }>;

export interface AuthorizationRequirement {
  readonly roles?: readonly string[];
  readonly scopes?: readonly string[];
}

export function anonymousAuthentication(): AuthenticationState {
  return { authenticated: false };
}

export function requireAuthentication(
  state: AuthenticationState,
): AuthenticatedPrincipal {
  if (!state.authenticated) {
    throw unauthorized("Authentication required");
  }

  return state.principal;
}

export function requireAuthorization(
  principal: AuthenticatedPrincipal,
  requirement: AuthorizationRequirement,
): void {
  if (
    requirement.roles?.some((role) => principal.roles.includes(role)) === false
  ) {
    throw forbidden("Access denied");
  }

  if (
    requirement.scopes?.every((scope) => principal.scopes.includes(scope)) ===
    false
  ) {
    throw forbidden("Access denied");
  }
}

export function hasAuthorization(
  principal: AuthenticatedPrincipal,
  requirement: AuthorizationRequirement,
): boolean {
  try {
    requireAuthorization(principal, requirement);
    return true;
  } catch {
    return false;
  }
}
