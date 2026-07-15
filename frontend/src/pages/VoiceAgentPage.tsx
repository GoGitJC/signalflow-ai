import { useEffect, useState } from "react";
import { Bot, Mic } from "lucide-react";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/hooks/toast-context";

type AgentDraft = {
  name: string;
  retellAgentId: string;
  greeting: string;
  systemPrompt: string;
  active: boolean;
};

const STORAGE_KEY = "signalflow_voice_agent_draft";

const defaults: AgentDraft = {
  name: "Front Desk Agent",
  retellAgentId: "",
  greeting: "Thanks for calling. How can I help you today?",
  systemPrompt:
    "You are a professional AI receptionist. Qualify leads, answer FAQs from the knowledge base, and book appointments when appropriate.",
  active: true,
};

export function VoiceAgentPage() {
  const { toast } = useToast();
  const [draft, setDraft] = useState<AgentDraft>(defaults);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      setDraft({ ...defaults, ...JSON.parse(raw) });
    } catch {
      /* ignore corrupt draft */
    }
  }, []);

  const save = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
    toast({ title: "Voice agent draft saved", description: "Persisted locally until agent APIs ship." });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Voice Agent"
        description="Configure greeting, prompt, and Retell identity for your AI receptionist."
        actions={
          <Button onClick={save}>
            Save configuration
          </Button>
        }
      />

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Agent configuration</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="agent-name">Display name</Label>
                <Input
                  id="agent-name"
                  value={draft.name}
                  onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="retell-id">Retell agent ID</Label>
                <Input
                  id="retell-id"
                  placeholder="agent_..."
                  value={draft.retellAgentId}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, retellAgentId: event.target.value }))
                  }
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="greeting">Greeting</Label>
              <Textarea
                id="greeting"
                value={draft.greeting}
                onChange={(event) => setDraft((current) => ({ ...current, greeting: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="prompt">System prompt</Label>
              <Textarea
                id="prompt"
                className="min-h-40"
                value={draft.systemPrompt}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, systemPrompt: event.target.value }))
                }
              />
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">Agent active</div>
                  <div className="text-xs text-muted-foreground">Controls local draft only in this phase</div>
                </div>
                <Switch
                  checked={draft.active}
                  onCheckedChange={(checked) => setDraft((current) => ({ ...current, active: checked }))}
                />
              </div>
              <StatusIndicator status={draft.active ? "online" : "idle"} label={draft.active ? "Ready" : "Paused"} />
              <Badge variant={draft.retellAgentId ? "success" : "warning"}>
                {draft.retellAgentId ? "Retell ID set" : "Retell ID missing"}
              </Badge>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Test voice</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Live Retell test calls arrive with provider credentials in a later sprint. This control validates UX
                readiness now.
              </p>
              <Button
                variant="outline"
                className="w-full"
                onClick={() =>
                  toast({
                    title: "Test voice queued",
                    description: "Connect Retell credentials to run a live agent test.",
                  })
                }
              >
                <Mic className="h-4 w-4" />
                Test voice
              </Button>
              <div className="flex items-center gap-2 rounded-xl border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
                <Bot className="h-4 w-4" />
                Draft stored in this browser until authenticated agent CRUD lands.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
