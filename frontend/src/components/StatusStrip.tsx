import { ApiStatus } from "./ApiStatus";
import { UserBadge } from "./UserBadge";

export function StatusStrip() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-2 border-b border-neutral-200 px-4 py-2 text-xs sm:flex-row sm:items-center sm:justify-between sm:px-6 dark:border-neutral-800">
      <ApiStatus />
      <UserBadge />
    </div>
  );
}
