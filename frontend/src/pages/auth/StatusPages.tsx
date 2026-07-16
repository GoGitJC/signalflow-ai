import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { AuthShell } from "@/auth/AuthShell";
import { useAuth } from "@/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function EmailVerificationPage() {
  const { user, reloadUser } = useAuth();
  const [token, setToken] = useState("verify-placeholder");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const result = await api.verifyEmail(token);
      await reloadUser();
      setMessage(result.detail);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to verify");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Verify your email"
      subtitle={
        user?.email_verified
          ? "Your email is already verified."
          : "Email delivery is a placeholder in this environment. Confirm with the token below."
      }
      footer={
        <p>
          <Link className="font-medium text-primary" to="/">
            Continue to dashboard
          </Link>
        </p>
      }
    >
      <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
        <div className="grid gap-2">
          <Label htmlFor="token">Verification token</Label>
          <Input id="token" value={token} onChange={(e) => setToken(e.target.value)} />
        </div>
        {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
        <Button className="w-full" type="submit" disabled={loading || Boolean(user?.email_verified)}>
          {user?.email_verified ? "Verified" : loading ? "Verifying…" : "Verify email"}
        </Button>
      </form>
    </AuthShell>
  );
}

export function SessionExpiredPage() {
  return (
    <AuthShell
      title="Session expired"
      subtitle="For your security, please sign in again to continue."
      footer={
        <Link className="font-medium text-primary" to="/login">
          Return to sign in
        </Link>
      }
    >
      <Button asChild className="w-full">
        <Link to="/login">Sign in</Link>
      </Button>
    </AuthShell>
  );
}

export function UnauthorizedPage() {
  return (
    <AuthShell
      title="Unauthorized"
      subtitle="You don’t have permission to view this area."
      footer={
        <Link className="font-medium text-primary" to="/">
          Back to dashboard
        </Link>
      }
    >
      <Button asChild variant="outline" className="w-full">
        <Link to="/">Go home</Link>
      </Button>
    </AuthShell>
  );
}
