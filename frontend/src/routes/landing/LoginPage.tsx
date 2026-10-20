import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getErrorMessage } from "../../api/errors";
import { LeftPanel } from "../../components/LeftPanel";
import { useAuth } from "../../context/AuthContext";

export function LoginPage() {
  const navigate = useNavigate();
  const { isBootstrapping, login, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isBootstrapping && user) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (caughtError) {
      const message = getErrorMessage(
        caughtError,
        "Invalid email or password. Please try again.",
      );
      setError(
        /invalid/i.test(message)
          ? "Invalid email or password. Please try again."
          : message,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-white-200 lg:flex">
      <LeftPanel />
      <main className="flex flex-1 items-center justify-center px-6 py-12 lg:px-12">
        <div className="w-full max-w-[34rem]">
          <p className="font-display text-[1.75rem] font-semibold tracking-[-0.04em] text-foreground lg:hidden">
            HumanFirst
          </p>
          <h1 className="mt-8 font-display text-[3rem] font-semibold tracking-[-0.05em] text-foreground">
            Welcome back
          </h1>
          <p className="mt-3 text-lg text-ml-grey-dark">
            Sign in to continue writing.
          </p>

          {error ? (
            <div className="mt-6 rounded-[14px] border border-destructive bg-destructive-bg px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <div className="mt-8 rounded-[24px] border border-ml-grey-lightest bg-white px-6 py-7 shadow-[0_24px_80px_rgba(15,23,42,0.08)] lg:px-8">
            <form className="grid gap-5" onSubmit={handleSubmit}>
              <label className="grid gap-2 text-sm font-medium text-foreground">
                <span>Email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="h-12 rounded-[14px] border border-ml-grey-lighter bg-white-200 px-4 text-base text-foreground outline-none transition placeholder:text-muted-foreground focus:border-ml-blue focus:ring-2 focus:ring-ml-blue/20"
                />
              </label>

              <label className="grid gap-2 text-sm font-medium text-foreground">
                <span>Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Your password"
                  className="h-12 rounded-[14px] border border-ml-grey-lighter bg-white-200 px-4 text-base text-foreground outline-none transition placeholder:text-muted-foreground focus:border-ml-blue focus:ring-2 focus:ring-ml-blue/20"
                />
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-2 inline-flex h-12 items-center justify-center rounded-[14px] bg-ml-red px-5 text-sm font-semibold text-white transition hover:bg-[#8f0909] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-red focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-ml-grey-lightest disabled:text-muted-foreground"
              >
                {isSubmitting ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <p className="mt-5 text-sm text-muted-foreground">
              New here?{" "}
              <Link className="font-medium text-ml-blue" to="/">
                Create an account →
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
