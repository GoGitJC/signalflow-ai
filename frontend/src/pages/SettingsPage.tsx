import { useState } from "react";
import { getBusinessId, setBusinessId } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/hooks/toast-context";

export function SettingsPage() {
  const { toast } = useToast();
  const [businessId, setLocalBusinessId] = useState(getBusinessId());
  const [profile, setProfile] = useState({
    name: "SignalFlow Demo Business",
    phone: "",
    forwarding: "",
    timezone: "America/Chicago",
    hours: "Mon–Fri 8:00–17:00",
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Business profile, transfer numbers, and provider configuration for this workspace."
      />

      <Tabs defaultValue="business">
        <TabsList>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="security">API & users</TabsTrigger>
        </TabsList>

        <TabsContent value="business" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Business profile</CardTitle>
              <CardDescription>Workspace identity used by the dashboard in this MVP phase.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="biz-id">Business ID</Label>
                <div className="flex gap-2">
                  <Input
                    id="biz-id"
                    value={businessId}
                    onChange={(event) => setLocalBusinessId(event.target.value)}
                    placeholder="UUID from POST /api/businesses"
                  />
                  <Button
                    onClick={() => {
                      setBusinessId(businessId.trim());
                      toast({ title: "Business ID saved", description: "Reload the page to refresh tenant data." });
                    }}
                  >
                    Save
                  </Button>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-name">Name</Label>
                <Input
                  id="biz-name"
                  value={profile.name}
                  onChange={(event) => setProfile((current) => ({ ...current, name: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-tz">Timezone</Label>
                <Input
                  id="biz-tz"
                  value={profile.timezone}
                  onChange={(event) => setProfile((current) => ({ ...current, timezone: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-phone">Primary phone</Label>
                <Input
                  id="biz-phone"
                  value={profile.phone}
                  onChange={(event) => setProfile((current) => ({ ...current, phone: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-forward">Transfer number</Label>
                <Input
                  id="biz-forward"
                  value={profile.forwarding}
                  onChange={(event) => setProfile((current) => ({ ...current, forwarding: event.target.value }))}
                />
              </div>
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="biz-hours">Business hours</Label>
                <Textarea
                  id="biz-hours"
                  value={profile.hours}
                  onChange={(event) => setProfile((current) => ({ ...current, hours: event.target.value }))}
                />
              </div>
              <div className="sm:col-span-2">
                <Button
                  variant="outline"
                  onClick={() =>
                    toast({
                      title: "Profile drafted locally",
                      description: "Authenticated business PATCH lands in the next product sprint.",
                    })
                  }
                >
                  Save profile draft
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="grid gap-4 lg:grid-cols-3">
          {[
            ["Retell", "Voice agent webhooks and live call orchestration."],
            ["Twilio", "SMS summaries and messaging delivery."],
            ["Cal.com", "Availability lookup and appointment booking."],
          ].map(([name, description]) => (
            <Card key={name}>
              <CardHeader>
                <CardTitle>{name}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input placeholder="Credential / account reference" />
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() =>
                    toast({
                      title: `${name} credential form ready`,
                      description: "Encrypted integration CRUD ships with authentication.",
                    })
                  }
                >
                  Save {name}
                </Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="security" className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>API keys</CardTitle>
              <CardDescription>Public API access is not enabled in the local MVP foundation.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={() => toast({ title: "API keys require auth sprint" })}>
                Generate key
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>Membership and roles arrive with JWT authentication.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Current operator context is implicit for this unauthenticated local phase. Tenant scoping still requires an
              explicit business ID.
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
