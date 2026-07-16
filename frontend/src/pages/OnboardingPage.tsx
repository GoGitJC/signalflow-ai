import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/toast-context";

const steps = [
  "Connect Retell",
  "Connect Cal.com",
  "Connect Twilio",
  "Add knowledge",
  "Test voice agent",
] as const;

export function OnboardingPage() {
  const { businessId } = useAuth();
  const { toast } = useToast();
  const [step, setStep] = useState(0);
  const [retellKey, setRetellKey] = useState("");
  const [calcomKey, setCalcomKey] = useState("");
  const [twilioSid, setTwilioSid] = useState("");
  const [twilioToken, setTwilioToken] = useState("");
  const [question, setQuestion] = useState("What are your business hours?");
  const [answer, setAnswer] = useState("Monday–Friday, 8am–5pm.");
  const [busy, setBusy] = useState(false);
  const title = useMemo(() => steps[step], [step]);

  const next = () => setStep((value) => Math.min(value + 1, steps.length - 1));
  const back = () => setStep((value) => Math.max(value - 1, 0));

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="First-run setup"
        description="Connect providers, add one knowledge entry, then verify your receptionist path."
      />
      <div className="flex flex-wrap gap-2">
        {steps.map((label, index) => (
          <button
            key={label}
            type="button"
            className={`rounded-full px-3 py-1 text-xs ${index === step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
            onClick={() => setStep(index)}
          >
            {index + 1}. {label}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Step {step + 1} of {steps.length}. You can skip and finish later in Settings.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 0 ? (
            <>
              <div className="grid gap-2">
                <Label htmlFor="retell-key">Retell API key</Label>
                <Input id="retell-key" type="password" value={retellKey} onChange={(e) => setRetellKey(e.target.value)} />
              </div>
              <Button
                disabled={!retellKey || busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await api.saveRetell(businessId, { api_key: retellKey, confirm_replace: true });
                    await api.testRetell(businessId);
                    toast({ title: "Retell connected" });
                    next();
                  } catch (err) {
                    toast({ title: "Retell setup failed", description: err instanceof Error ? err.message : "Error", variant: "danger" });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save & test Retell
              </Button>
            </>
          ) : null}

          {step === 1 ? (
            <>
              <div className="grid gap-2">
                <Label htmlFor="cal-key">Cal.com API key</Label>
                <Input id="cal-key" type="password" value={calcomKey} onChange={(e) => setCalcomKey(e.target.value)} />
              </div>
              <Button
                disabled={!calcomKey || busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await api.saveCalcom(businessId, { api_key: calcomKey, confirm_replace: true });
                    await api.testCalcom(businessId);
                    toast({ title: "Cal.com connected" });
                    next();
                  } catch (err) {
                    toast({ title: "Cal.com setup failed", description: err instanceof Error ? err.message : "Error", variant: "danger" });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save & test Cal.com
              </Button>
            </>
          ) : null}

          {step === 2 ? (
            <>
              <p className="text-sm text-muted-foreground">
                Twilio live SMS is gated behind production acceptance. Store Account SID / Auth Token in platform secrets
                for now; confirmation SMS is validated on the Final Production Acceptance Checklist.
              </p>
              <div className="grid gap-2">
                <Label htmlFor="twilio-sid">Twilio Account SID (optional note)</Label>
                <Input id="twilio-sid" value={twilioSid} onChange={(e) => setTwilioSid(e.target.value)} placeholder="ACxxxxx" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="twilio-token">Twilio Auth Token (do not commit)</Label>
                <Input id="twilio-token" type="password" value={twilioToken} onChange={(e) => setTwilioToken(e.target.value)} />
              </div>
              <Button
                onClick={() => {
                  localStorage.setItem(
                    "signalflow_onboarding_twilio",
                    JSON.stringify({ noted: Boolean(twilioSid || twilioToken) }),
                  );
                  toast({ title: "Twilio step saved locally" });
                  next();
                }}
              >
                Continue
              </Button>
            </>
          ) : null}

          {step === 3 ? (
            <>
              <div className="grid gap-2">
                <Label htmlFor="kb-q">Knowledge question</Label>
                <Input id="kb-q" value={question} onChange={(e) => setQuestion(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="kb-a">Answer</Label>
                <Textarea id="kb-a" value={answer} onChange={(e) => setAnswer(e.target.value)} />
              </div>
              <Button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await api.addKnowledge(businessId, {
                      category: "general",
                      question,
                      answer,
                      active: true,
                    });
                    toast({ title: "Knowledge entry created" });
                    next();
                  } catch (err) {
                    toast({ title: "KB save failed", description: err instanceof Error ? err.message : "Error", variant: "danger" });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save knowledge entry
              </Button>
            </>
          ) : null}

          {step === 4 ? (
            <>
              <p className="text-sm text-muted-foreground">
                Open Voice Agent to review greeting and prompt, then place a no-booking test call with{" "}
                <code>ALLOW_LIVE_BOOKING=false</code>. Use Help for webhook simulation in mock mode.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button asChild>
                  <Link to="/voice-agent">Open Voice Agent</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/">Go to dashboard</Link>
                </Button>
              </div>
            </>
          ) : null}

          <div className="flex justify-between pt-2">
            <Button variant="outline" onClick={back} disabled={step === 0}>
              Back
            </Button>
            {step < steps.length - 1 ? (
              <Button variant="secondary" onClick={next}>
                Skip for now
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
