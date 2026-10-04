type ConnectionStatus = "connected" | "connecting" | "disconnected";

type ConnectionBadgeProps = {
  status: ConnectionStatus;
};

const labels: Record<ConnectionStatus, string> = {
  connected: "Connected",
  connecting: "Connecting",
  disconnected: "Disconnected",
};

export default function ConnectionBadge({
  status,
}: ConnectionBadgeProps) {
  return (
    <span className={`connection-badge connection-${status}`}>
      <span className="connection-dot" aria-hidden="true" />
      {labels[status]}
    </span>
  );
}
