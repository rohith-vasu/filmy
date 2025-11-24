import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, LoginSchemaType } from "@/schemas/authSchemas";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { authAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const Login = () => {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const openRegisterPrompt = useAuthStore((s) => s.openRegisterPrompt);
  const [loading, setLoading] = useState(false);

  const form = useForm<LoginSchemaType>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: LoginSchemaType) => {
    try {
      setLoading(true);

      const res = await authAPI.login(data.email, data.password);

      // Backend returned an explicit handled error
      if (res?.status && res.status !== "success") {
        const msg = String(res.message || "").toLowerCase();

        if (msg.includes("user not found") || msg.includes("not found")) {
          // Show register modal (ShadCN)
          openRegisterPrompt();
          return;
        }

        toast.error(res.message || "Invalid login credentials");
        return;
      }

      // Successful login → fetch user profile
      const userRes = await authAPI.getCurrentUser();
      const u = userRes.data || userRes;

      setUser({
        id: u.id,
        email: u.email,
        first_name: u.firstname,
        last_name: u.lastname,
      });

      toast.success(`Welcome back, ${u.firstname}`);
      navigate("/dashboard");
    } catch (err: any) {
      const detail = String(err?.response?.data?.detail || "").toLowerCase();

      if (detail.includes("user not found")) {
        openRegisterPrompt();
        return;
      }

      toast.error("Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background Glow - matching hero section */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/10 blur-3xl animate-glow-pulse" />

      <div className="w-full max-w-md relative z-10">

        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <img src="/filmy-icon.ico" alt="Filmy Logo" className="w-9 h-9" />
          <span className="text-2xl font-heading font-bold">filmy</span>
        </Link>

        <div className="bg-card border border-border rounded-2xl p-8">
          <h1 className="text-3xl font-heading font-bold text-center">Welcome Back</h1>
          <p className="text-muted-foreground text-center mb-8">
            Log in to get personalized recommendations
          </p>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

            {/* Email */}
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                {...form.register("email")}
                placeholder="you@example.com"
                className={form.formState.errors.email ? "border-red-500" : ""}
              />
              <p className="text-red-500 text-xs">{form.formState.errors.email?.message}</p>
            </div>

            {/* Password */}
            <div>
              <Label>Password</Label>
              <Input
                type="password"
                {...form.register("password")}
                placeholder="••••••••"
                className={form.formState.errors.password ? "border-red-500" : ""}
              />
              <p className="text-red-500 text-xs">{form.formState.errors.password?.message}</p>
            </div>

            <Button
              className="w-full gradient-cinematic glow-primary text-lg py-6 mt-6"
              disabled={loading}
            >
              {loading ? "Logging in..." : "Log In"}
            </Button>

          </form>

          <div className="mt-6 text-center">
            <Link to="/register" className="text-sm text-muted-foreground hover:text-primary">
              Don't have an account? Sign up
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-muted-foreground hover:text-primary">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
