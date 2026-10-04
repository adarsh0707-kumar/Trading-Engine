type EmptyStateProps = {
  title: string;
  message?: string;
};

export default function EmptyState({
  title,
  message,
}: EmptyStateProps) {
  return (
    <div className="state-message">
      <strong>{title}</strong>
      {message && <span>{message}</span>}
    </div>
  );
}
