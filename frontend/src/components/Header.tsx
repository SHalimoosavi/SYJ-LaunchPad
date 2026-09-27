"use client";

import { ConnectButton } from "@rainbow-me/rainbowkit";

export function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-neutral-200 bg-background/80 backdrop-blur dark:border-neutral-800">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        <span className="text-base font-semibold tracking-tight">SYJ LaunchPad</span>
        <ConnectButton showBalance={false} />
      </div>
    </header>
  );
}
