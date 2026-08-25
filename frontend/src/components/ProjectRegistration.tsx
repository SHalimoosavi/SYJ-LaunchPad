"use client";

import { useState } from "react";
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

/**
 * Minimal Phase 3 project registration UI: a name/description/website
 * form and a list of the authenticated user's own projects. Deliberately
 * not a dashboard — token creation, presale configuration, and analytics
 * are later-phase scope (see docs/ROADMAP.md) and don't belong here yet.
 */
export function ProjectRegistration() {
  const { status } = useAuth();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ["projects", "me"],
    queryFn: () => apiFetch<ProjectResponse[]>("/api/v1/projects/me"),
    enabled: status === "authenticated",
  });

  if (status !== "authenticated") {
    return (
      <p className="text-sm text-neutral-500">
        Connect and sign in with your wallet to register a project.
      </p>
    );
  }

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
      await queryClient.invalidateQueries({ queryKey: ["projects", "me"] });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong registering the project.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-md space-y-6">
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          maxLength={100}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
        <textarea
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={5000}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
        <input
          type="url"
          placeholder="Website (optional)"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          maxLength={2048}
          className="w-full rounded border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={isSubmitting || name.trim().length === 0}
          className="w-full rounded bg-foreground px-3 py-2 text-sm font-medium text-background disabled:opacity-50"
        >
          {isSubmitting ? "Registering…" : "Register project"}
        </button>
      </form>

      <div>
        <h2 className="mb-2 text-sm font-medium text-neutral-500">Your projects</h2>
        {projectsLoading ? (
          <p className="text-sm text-neutral-500">Loading…</p>
        ) : projects && projects.length > 0 ? (
          <ul className="space-y-2">
            {projects.map((project) => (
              <li
                key={project.id}
                className="rounded border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-700"
              >
                <div className="font-medium">{project.name}</div>
                {project.description && (
                  <div className="text-neutral-500">{project.description}</div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-neutral-500">No projects registered yet.</p>
        )}
      </div>
    </div>
  );
}
