import type { ApiConnection } from "@/lib/api/client";

type ConnectionStatusProps = {
  connection: ApiConnection;
};

export function ConnectionStatus({ connection }: ConnectionStatusProps) {
  const isOnline = connection.state === "online";
  const fullLabel = isOnline
    ? `API connected · v${connection.version}`
    : "Preview mode · API offline";

  return (
    <div
      className={`connection-status ${isOnline ? "is-online" : "is-offline"}`}
      role="status"
      aria-live="polite"
      aria-label={fullLabel}
    >
      <span className="connection-dot" aria-hidden="true" />
      <span className="connection-copy-full">{fullLabel}</span>
      <span className="connection-copy-mobile" aria-hidden="true">
        {isOnline ? "API online" : "API offline"}
      </span>
    </div>
  );
}
