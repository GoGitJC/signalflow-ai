import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/PageHeader";

export function HelpPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Help"
        description="Quick references for local development, webhooks, and dashboard shortcuts."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Get live data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>1. Create a business via `POST /api/businesses`.</p>
            <p>2. Set `VITE_BUSINESS_ID` or save the UUID in Settings.</p>
            <p>3. Run `./scripts/simulate_call.sh` with that business ID.</p>
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
            <CardTitle>Docs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Architecture, API, and UI guidelines live under `/docs` in the repository.</p>
            <p>OpenAPI remains available at `http://localhost:8000/docs`.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Support posture</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            This foundation ships mock providers by default. Live Retell, Twilio, and Cal.com require encrypted
            credentials and authentication in later sprints.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
