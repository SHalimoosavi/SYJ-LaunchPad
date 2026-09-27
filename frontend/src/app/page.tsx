import { Header } from "@/components/Header";
import { ProjectRegistration } from "@/components/ProjectRegistration";
import { StatusStrip } from "@/components/StatusStrip";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Header />
      <StatusStrip />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Register and manage your LaunchPad projects. Presale, token, and
            claim features arrive in later phases once their parameters are
            defined — see the project roadmap.
          </p>
        </div>
        <ProjectRegistration />
      </main>
    </div>
  );
}
