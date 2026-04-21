import { IncidentGovernance } from "@/Features/incidents/IncidentGovernance";
import { AppShell } from "@/shared/components/layout/AppShell";

export default function DashboardPage() {
  return (
    <AppShell>
      <IncidentGovernance />
    </AppShell>
  );
}
