import { useCallback, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { authMe, type User } from "../api/client";
import { useAuth } from "../context/AuthContext";

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

type FormState = { email: string; password: string };

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState<FormState>({ email: "", password: "" });
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const validate = useCallback(
    (state: FormState) => {
      const next: Partial<FormState> = {};
      if (!EMAIL_REGEX.test(state.email.trim().toLowerCase())) {
        next.email = "Enter a valid email.";
      }
      if (state.password.trim().length < 8) {
        next.password = "Password must be at least 8 characters.";
      }
      return next;
    },
    [],
  );

  const handlePostAuth = useCallback(
    async (fallbackUser?: User | null) => {
      try {
        const me = await authMe();
        const user = me.user ?? fallbackUser ?? null;
        if (user?.onboarding_completed) {
          navigate("/captain/dashboard");
        } else {
          navigate("/onboarding");
        }
      } catch {
        navigate("/");
      }
    },
    [navigate],
  );

  const mutation = useMutation({
    mutationFn: (input: { email: string; password: string }) => login(input),
    onSuccess: async (res) => {
      setServerError(null);
      await handlePostAuth(res.ok ? res.user : null);
    },
    onError: (error: Error & { field?: string }) => {
      setServerError(error.message || "Invalid credentials.");
      if (error.field) {
        setErrors((prev) => ({ ...prev, [error.field as keyof FormState]: error.message || "Invalid input" }));
      }
    },
  });

  const onChange = (key: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const nextErrors = validate(form);
    setErrors(nextErrors);
    setServerError(null);
    if (Object.keys(nextErrors).length > 0) return;
    mutation.mutate({ email: form.email.trim().toLowerCase(), password: form.password });
  };

  const buttonLabel = useMemo(() => (mutation.isPending ? "Signing in..." : "Sign in"), [mutation.isPending]);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-card-header">
            <p className="eyebrow">Welcome back</p>
            <h1>Sign in</h1>
            <p className="muted small">Use your email and password to continue.</p>
          </div>

          {serverError ? <div className="auth-alert error-alert">{serverError}</div> : null}

          <form className="auth-form" onSubmit={onSubmit} noValidate>
            <div className="form-field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="Enter your email"
                value={form.email}
                onChange={(e) => onChange("email", e.target.value)}
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? "email-error" : undefined}
              />
              {errors.email ? (
                <span id="email-error" className="field-error">
                  {errors.email}
                </span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="login-password">Password</label>
              <div className="password-wrapper">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => onChange("password", e.target.value)}
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? "password-error" : undefined}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              {errors.password ? (
                <span id="password-error" className="field-error">
                  {errors.password}
                </span>
              ) : null}
            </div>

            <button type="submit" className="button primary full-width" disabled={mutation.isPending}>
              {buttonLabel}
            </button>
          </form>

          <div className="auth-footer">
            <span className="muted small">Need an account?</span>
            <Link to="/signup" className="link">
              Create account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
