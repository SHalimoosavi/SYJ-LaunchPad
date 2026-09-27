const DOT_COLOR: Record<"ok" | "pending" | "error", string> = {
  ok: "bg-green-500",
  pending: "bg-neutral-400",
  error: "bg-red-500",
};

export function StatusDot({ state }: { state: "ok" | "pending" | "error" }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${DOT_COLOR[state]}`}
    />
  );
}
