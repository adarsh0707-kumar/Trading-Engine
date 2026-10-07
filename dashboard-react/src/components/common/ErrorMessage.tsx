type ErrorMessageProps = {
  message: string;
  action?: string;
  onAction?: () => void;
};

export default function ErrorMessage({
  message,
  action,
  onAction,
}: ErrorMessageProps) {
  return (
    <div className="state-message state-error" role="alert">
      <span>{message}</span>
      {action && onAction && (
        <button type="button" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}
