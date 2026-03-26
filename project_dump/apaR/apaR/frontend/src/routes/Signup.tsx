import { useCallback, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { authMe, type User } from "../api/client";
import { useAuth } from "../context/AuthContext";

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PASSWORD_MIN = 8;

type FormState = { email: string; password: string; username: string };

export function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState<FormState>({ email: "", password: "", username: "" });
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const validate = useCallback((state: FormState) => {
    const next: Partial<FormState> = {};
    if (!EMAIL_REGEX.test(state.email.trim().toLowerCase())) {
      next.email = "Enter a valid email.";
    }
    if (state.password.trim().length < PASSWORD_MIN) {
      next.password = `Password must be at least ${PASSWORD_MIN} characters.`;
    }
    if (state.username && state.username.trim().length < 3) {
      next.username = "Username should be 3+ characters or leave blank.";
    }
    return next;
  }, []);

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
    mutationFn: (input: { email: string; password: string; username?: string | null }) => signup(input),
    onSuccess: async (res) => {
      setServerError(null);
      await handlePostAuth(res.ok ? res.user : null);
    },
    onError: (error: Error & { field?: string }) => {
      const errorMsg = error.message || "Could not create account.";
      setServerError(errorMsg);
      // Log error details for debugging
      console.error("Signup error:", {
        message: errorMsg,
        code: (error as any).code,
        field: error.field,
        cause: (error as any).cause,
      });
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
    mutation.mutate({
      email: form.email.trim().toLowerCase(),
      password: form.password,
      username: form.username.trim() || undefined,
    });
  };

  const buttonLabel = useMemo(() => (mutation.isPending ? "Creating..." : "Create account"), [mutation.isPending]);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-card-header">
            <p className="eyebrow">Join apaR</p>
            <h1>Create your account</h1>
            <p className="muted small">We&apos;ll use this to save your onboarding and captain settings.</p>
          </div>

          {serverError ? <div className="auth-alert error-alert">{serverError}</div> : null}

          <form className="auth-form" onSubmit={onSubmit} noValidate>
            <div className="form-field">
              <label htmlFor="signup-email">Email</label>
              <input
                id="signup-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="Enter your email"
                value={form.email}
                onChange={(e) => onChange("email", e.target.value)}
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? "signup-email-error" : undefined}
              />
              {errors.email ? (
                <span id="signup-email-error" className="field-error">
                  {errors.email}
                </span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="signup-password">Password</label>
              <div className="password-wrapper">
                <input
                  id="signup-password"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  autoComplete="new-password"
                  placeholder="At least 8 characters"
                  value={form.password}
                  onChange={(e) => onChange("password", e.target.value)}
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? "signup-password-error" : undefined}
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
                <span id="signup-password-error" className="field-error">
                  {errors.password}
                </span>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="signup-username">Username (optional)</label>
              <input
                id="signup-username"
                type="text"
                name="username"
                autoComplete="username"
                placeholder="Leave blank to use your email"
                value={form.username}
                onChange={(e) => onChange("username", e.target.value)}
                aria-invalid={Boolean(errors.username)}
                aria-describedby={errors.username ? "signup-username-error" : undefined}
              />
              {errors.username ? (
                <span id="signup-username-error" className="field-error">
                  {errors.username}
                </span>
              ) : (
                <span className="field-hint">Leave blank to use your email as your handle.</span>
              )}
            </div>

            <button type="submit" className="button primary full-width" disabled={mutation.isPending}>
              {buttonLabel}
            </button>
          </form>

          <div className="auth-footer">
            <span className="muted small">Already have an account?</span>
            <Link to="/login" className="link">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
