import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/toast-context";

const steps = [
  "Welcome",
  "Connect Retell",
  "Connect Cal.com",
  "Connect Twilio",
  "Add knowledge",
  "Test call checklist",
] as const;

const testChecklist = [
  "Voice agent greeting and prompt look correct",
  "Public webhook URL registered with Retell",
  "Place a no-booking test call (ALLOW_LIVE_BOOKING=false)",
  "Call appears on the Calls page with transcript/summary",
  "Optional: simulate webhook via Help in mock mode",
];

export function OnboardingPage() {
  const { businessId } = useAuth();
  const { toast } = useToast();
  const [step, setStep] = useState(0);
  const [retellKey, setRetellKey] = useState("");
  const [calcomKey, setCalcomKey] = useState("");
  const [twilioSid, setTwilioSid] = useState("");
  const [twilioToken, setTwilioToken] = useState("");
  const [question, setQuestion] = useState("What are your service hours?");
  const [answer, setAnswer] = useState("Monday–Friday, 7am–6pm. Emergency dispatch after hours.");
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [busy, setBusy] = useState(false);
  const title = useMemo(() => steps[step], [step]);

  const next = () => setStep((value) => Math.min(value + 1, steps.length - 1));
  const back = () => setStep((value) => Math.max(value - 1, 0));

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="First-run setup"
        description="Welcome to ForgeLinq closed beta — connect providers, add knowledge, then verify a test call."
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
            <div className="space-y-4">
              <BrandLogo />
              <p className="text-sm text-muted-foreground">
                ForgeLinq answers inbound calls, books appointments, and gives your team a CRM dashboard.
                This wizard takes about five minutes. Keep live booking off until Final Acceptance.
              </p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                <li>Retell for the voice agent</li>
                <li>Cal.com for scheduling</li>
                <li>Twilio for SMS (placeholder until acceptance)</li>
                <li>One knowledge-base FAQ to start</li>
              </ul>
              <Button onClick={next}>Get started</Button>
            </div>
          ) : null}

          {step === 1 ? (
            <>
              <div className="grid gap-2">
                <Label htmlFor="retell-key">Retell API key</Label>
                <Input
                  id="retell-key"
                  type="password"
                  value={retellKey}
                  onChange={(e) => setRetellKey(e.target.value)}
                />
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
                    toast({
                      title: "Retell setup failed",
                      description: err instanceof Error ? err.message : "Error",
                      variant: "danger",
                    });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save & test Retell
              </Button>
            </>
          ) : null}

          {step === 2 ? (
            <>
              <div className="grid gap-2">
                <Label htmlFor="cal-key">Cal.com API key</Label>
                <Input
                  id="cal-key"
                  type="password"
                  value={calcomKey}
                  onChange={(e) => setCalcomKey(e.target.value)}
                />
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
                    toast({
                      title: "Cal.com setup failed",
                      description: err instanceof Error ? err.message : "Error",
                      variant: "danger",
                    });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save & test Cal.com
              </Button>
            </>
          ) : null}

          {step === 3 ? (
            <>
              <p className="text-sm text-muted-foreground">
                Twilio live SMS is gated behind Final Acceptance. Store Account SID / Auth Token notes here;
                production secrets belong in the host secret store — never commit them.
              </p>
              <div className="grid gap-2">
                <Label htmlFor="twilio-sid">Twilio Account SID (optional note)</Label>
                <Input
                  id="twilio-sid"
                  value={twilioSid}
                  onChange={(e) => setTwilioSid(e.target.value)}
                  placeholder="ACxxxxx"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="twilio-token">Twilio Auth Token (do not commit)</Label>
                <Input
                  id="twilio-token"
                  type="password"
                  value={twilioToken}
                  onChange={(e) => setTwilioToken(e.target.value)}
                />
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

          {step === 4 ? (
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
                    toast({
                      title: "KB save failed",
                      description: err instanceof Error ? err.message : "Error",
                      variant: "danger",
                    });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save knowledge entry
              </Button>
            </>
          ) : null}

          {step === 5 ? (
            <>
              <p className="text-sm text-muted-foreground">
                Complete this checklist before inviting staff or enabling live booking.
              </p>
              <ul className="space-y-2">
                {testChecklist.map((item, index) => (
                  <li key={item}>
                    <label className="flex items-start gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={Boolean(checked[index])}
                        onChange={(e) =>
                          setChecked((current) => ({ ...current, [index]: e.target.checked }))
                        }
                      />
                      <span>{item}</span>
                    </label>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-2">
                <Button asChild>
                  <Link to="/voice-agent">Open Voice Agent</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link to="/readiness">Final Acceptance</Link>
                </Button>
                <Button asChild variant="secondary">
                  <Link to="/">Go to dashboard</Link>
                </Button>
              </div>
            </>
          ) : null}

          <div className="flex justify-between pt-2">
            <Button variant="outline" onClick={back} disabled={step === 0}>
              Back
            </Button>
            {step > 0 && step < steps.length - 1 ? (
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
