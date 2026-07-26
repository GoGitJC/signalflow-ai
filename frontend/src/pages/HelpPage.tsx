import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export function HelpPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Help"
        description="Closed-beta references for onboarding, webhooks, exports, and go-live checks."
      />
      <div className="flex flex-wrap gap-2">
        <Button asChild>
          <Link to="/onboarding">First-run setup</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/readiness">Final Acceptance</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/settings">Settings & exports</Link>
        </Button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Get live data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>1. Register a workspace or seed the HVAC demo tenant.</p>
            <p>2. Complete `/onboarding` (Retell, Cal.com, knowledge).</p>
            <p>3. Run `./scripts/simulate_call.sh` in mock mode, or place a no-booking live test call.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Keyboard shortcuts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>`/` focuses the top search on desktop layouts.</p>
            <p>Theme preference persists in local storage.</p>
            <p>Use Refresh in the top bar after posting webhooks.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Docs (repository)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>`docs/onboarding.md` — customer first-run</p>
            <p>`docs/demo-data.md` — HVAC demo seed</p>
            <p>`docs/deployment.md` — HTTPS, cookies, hosts</p>
            <p>`docs/production-readiness.md` — go-live checklist</p>
            <p>OpenAPI: {API_BASE ? `${API_BASE}/docs` : "`VITE_API_URL`/docs"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Support posture</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Closed beta keeps `ALLOW_LIVE_BOOKING=false` until Final Acceptance. Twilio SMS remains a
            placeholder until the acceptance checklist is signed off.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
