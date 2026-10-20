import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getErrorMessage } from "../../api/errors";
import { LeftPanel } from "../../components/LeftPanel";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../components/shared/utils";

type FormState = {
  email: string;
  name: string;
  password: string;
};

export function LandingPage() {
  const navigate = useNavigate();
  const { isBootstrapping, register, user } = useAuth();
  const [form, setForm] = useState<FormState>({
    email: "",
    name: "",
    password: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAuthed = Boolean(user);
  const validationErrors = useMemo(() => {
    const nextErrors: Partial<FormState> = {};
    if (!form.name.trim()) nextErrors.name = "Name is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      nextErrors.email = "Enter a valid email address.";
    }
    if (form.password.length < 8) {
      nextErrors.password = "Password must be at least 8 characters.";
    }
    return nextErrors;
  }, [form]);

  if (!isBootstrapping && isAuthed) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldErrors(validationErrors);
    setGeneralError(null);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register(form.name.trim(), form.email.trim(), form.password);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setGeneralError(getErrorMessage(error, "Unable to create your account."));
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
            Create your account
          </h1>
          <p className="mt-3 text-lg text-ml-grey-dark">
            Start writing. Connect your AI after the core piece is yours.
          </p>

          {generalError ? (
            <div className="mt-6 rounded-[14px] border border-destructive bg-destructive-bg px-4 py-3 text-sm text-destructive">
              {generalError}
            </div>
          ) : null}

          <div className="mt-8 rounded-[24px] border border-ml-grey-lightest bg-white px-6 py-7 shadow-[0_24px_80px_rgba(15,23,42,0.08)] lg:px-8">
            <form className="grid gap-5" onSubmit={handleSubmit}>
              <AuthField
                label="Name"
                placeholder="Your full name"
                value={form.name}
                error={fieldErrors.name}
                onChange={(value) => setForm((current) => ({ ...current, name: value }))}
              />
              <AuthField
                label="Email"
                placeholder="you@example.com"
                type="email"
                value={form.email}
                error={fieldErrors.email}
                onChange={(value) => setForm((current) => ({ ...current, email: value }))}
              />
              <AuthField
                label="Password"
                placeholder="8+ characters"
                type="password"
                value={form.password}
                error={fieldErrors.password}
                onChange={(value) =>
                  setForm((current) => ({ ...current, password: value }))
                }
              />

              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-2 inline-flex h-12 items-center justify-center rounded-[14px] bg-ml-red px-5 text-sm font-semibold text-white transition hover:bg-[#8f0909] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-red focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-ml-grey-lightest disabled:text-muted-foreground"
              >
                {isSubmitting ? "Creating account..." : "Create account"}
              </button>
            </form>

            <p className="mt-5 text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link className="font-medium text-ml-blue" to="/login">
                Sign in →
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

type AuthFieldProps = {
  error?: string;
  label: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: "email" | "password" | "text";
  value: string;
};

function AuthField({
  error,
  label,
  onChange,
  placeholder,
  type = "text",
  value,
}: AuthFieldProps) {
  return (
    <label className="grid gap-2 text-sm font-medium text-foreground">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className={cn(
          "h-12 rounded-[14px] border bg-white-200 px-4 text-base text-foreground outline-none transition placeholder:text-muted-foreground focus:border-ml-blue focus:ring-2 focus:ring-ml-blue/20",
          error
            ? "border-destructive bg-destructive-bg"
            : "border-ml-grey-lighter",
        )}
      />
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
}
