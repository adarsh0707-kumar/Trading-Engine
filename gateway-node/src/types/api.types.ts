export type ApiErrorCode =
  | "INVALID_ARGUMENT"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "DEPENDENCY_UNAVAILABLE"
  | "INTERNAL_ERROR";

export interface ApiErrorBody {
  readonly error: {
    readonly code: ApiErrorCode;
    readonly message: string;
    readonly request_id?: string;
  };
}

export interface ApiSuccessResponse<T> {
  readonly data: T;
}
