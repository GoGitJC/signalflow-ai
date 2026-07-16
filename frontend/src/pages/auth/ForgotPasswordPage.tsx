import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { AuthShell } from "@/auth/AuthShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [devToken, setDevToken] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    setDevToken("");
    try {
      const result = await api.forgotPassword(email);
      setMessage(result.detail);
      if (result.reset_token) setDevToken(result.reset_token);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to start reset");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Reset your password"
      subtitle="We’ll prepare a secure reset link for your account."
      footer={
        <p>
          Remembered it?{" "}
          <Link className="font-medium text-primary" to="/login">
            Back to sign in
          </Link>
        </p>
      }
    >
      <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
        {devToken ? (
          <p className="rounded-xl bg-muted p-3 text-xs break-all text-muted-foreground">
            Dev reset token:{" "}
            <Link className="text-primary" to={`/reset-password?token=${encodeURIComponent(devToken)}`}>
              continue to reset
            </Link>
          </p>
        ) : null}
        <Button className="w-full" type="submit" disabled={loading}>
          {loading ? "Sending…" : "Send reset link"}
        </Button>
      </form>
    </AuthShell>
  );
}
