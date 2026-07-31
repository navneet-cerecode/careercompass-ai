import type { ApiConnection } from "@/lib/api/client";

type ConnectionStatusProps = {
  connection: ApiConnection;
};

export function ConnectionStatus({ connection }: ConnectionStatusProps) {
  const isOnline = connection.state === "online";

  return (
    <div
      className={`connection-status ${isOnline ? "is-online" : "is-offline"}`}
      role="status"
      aria-live="polite"
    >
      <span className="connection-dot" aria-hidden="true" />
      <span>
        {isOnline
          ? `API connected · v${connection.version}`
          : "Preview mode · API offline"}
      </span>
    </div>
  );
}
