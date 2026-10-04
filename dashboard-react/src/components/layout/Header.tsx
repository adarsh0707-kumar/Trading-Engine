import ConnectionBadge from "../common/ConnectionBadge";

export default function Header() {
  return (
    <header className="header">
      <div>
        <strong>Trading Engine</strong>
      </div>

      <ConnectionBadge status="disconnected" />
    </header>
  );
}
