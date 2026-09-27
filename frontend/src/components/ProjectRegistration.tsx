"use client";

import { useId, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

interface ProjectResponse {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  website_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        isActive
          ? "bg-green-500/10 text-green-600 dark:text-green-400"
          : "bg-neutral-500/10 text-neutral-500"
      }`}
    >
      {isActive ? "Active" : "Inactive"}
    </span>
  );
}

function ProjectCardSkeleton() {
  return (
    <div
      className="animate-pulse rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
      aria-hidden="true"
    >
      <div className="mb-2 h-4 w-1/3 rounded bg-neutral-200 dark:bg-neutral-800" />
      <div className="h-3 w-2/3 rounded bg-neutral-200 dark:bg-neutral-800" />
    </div>
  );
}

function RegistrationForm({ onRegistered }: { onRegistered: () => void }) {
  const nameId = useId();
  const descriptionId = useId();
  const websiteId = useId();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiFetch<ProjectResponse>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({
          name,
          description: description || undefined,
          website_url: websiteUrl || undefined,
        }),
      });
      setName("");
      setDescription("");
      setWebsiteUrl("");
      onRegistered();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong registering the project.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
      aria-label="Register a new project"
    >
      <h2 className="text-sm font-semibold">Register a project</h2>

      <div>
        <label htmlFor={nameId} className="mb-1 block text-xs text-neutral-500">
          Name
        </label>
        <input
          id={nameId}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          maxLength={100}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
      </div>

      <div>
        <label htmlFor={descriptionId} className="mb-1 block text-xs text-neutral-500">
          Description (optional)
        </label>
        <textarea
          id={descriptionId}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={5000}
          rows={3}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
      </div>

      <div>
        <label htmlFor={websiteId} className="mb-1 block text-xs text-neutral-500">
          Website (optional)
        </label>
        <input
          id={websiteId}
          type="url"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          maxLength={2048}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-500">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isSubmitting || name.trim().length === 0}
        className="w-full rounded bg-foreground px-3 py-2 text-sm font-medium text-background disabled:opacity-50"
      >
        {isSubmitting ? "Registering…" : "Register project"}
      </button>
    </form>
  );
}

function ProjectList() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["projects", "me"],
    queryFn: () => apiFetch<ProjectResponse[]>("/api/v1/projects/me"),
  });

  if (isLoading) {
    return (
      <div className="space-y-2" aria-busy="true" aria-live="polite">
        <ProjectCardSkeleton />
        <ProjectCardSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500"
      >
        <p className="mb-2">Couldn&apos;t load your projects.</p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="rounded border border-red-500/40 px-2 py-1 text-xs font-medium"
        >
          {isFetching ? "Retrying…" : "Retry"}
        </button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-500 dark:border-neutral-700">
        No projects registered yet. Use the form to register your first one.
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {data.map((project) => (
        <li
          key={project.id}
          className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-medium">{project.name}</div>
              <div className="font-mono text-xs text-neutral-500">{project.slug}</div>
            </div>
            <StatusBadge isActive={project.is_active} />
          </div>
          {project.description && (
            <p className="mt-2 text-sm text-neutral-500">{project.description}</p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-neutral-400">
            <span>Registered {formatDate(project.created_at)}</span>
            {project.website_url && (
              <a
                href={project.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-neutral-500 underline underline-offset-2 hover:text-foreground"
              >
                Website
              </a>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

/**
 * Dashboard's project section: registration form + the caller's own
 * projects. Every field shown here comes directly from the existing
 * Project Registration API (backend/app/features/projects) — nothing is
 * fabricated. Token balances, on-chain status, presale/sale data, and
 * project analytics are NOT shown because no backend capability exists
 * for them yet (Phase 4+ territory) — see docs/ROADMAP.md.
 */
export function ProjectRegistration() {
  const { status } = useAuth();
  const queryClient = useQueryClient();

  if (status !== "authenticated") {
    return (
      <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-500 dark:border-neutral-700">
        Connect and sign in with your wallet to register a project.
      </div>
    );
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <RegistrationForm
        onRegistered={() => void queryClient.invalidateQueries({ queryKey: ["projects", "me"] })}
      />
      <div>
        <h2 className="mb-3 text-sm font-semibold">Your projects</h2>
        <ProjectList />
      </div>
    </div>
  );
}
