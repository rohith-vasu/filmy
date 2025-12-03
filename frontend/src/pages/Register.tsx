import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registerSchema, RegisterSchemaType } from "@/schemas/authSchemas";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { authAPI } from "@/lib/api";

const Register = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const form = useForm<RegisterSchemaType>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur", // validate on blur + submit
  });

  const onSubmit = async (data: RegisterSchemaType) => {
    try {
      setLoading(true);

      const res = await authAPI.signup(
        data.firstname,
        data.lastname,
        data.email,
        data.password
      );

      if (res.status === "success") {
        toast.success("Account created successfully!");
        navigate("/login");
      } else {
        toast.error(res.message || "Registration failed");
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Registration failed");
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
        <Link to="/" className="flex items-center gap-2 justify-center mb-8">
          <img src="/filmy-icon.ico" alt="Filmy Logo" className="w-9 h-9" />
          <span className="text-2xl font-heading font-bold">filmy</span>
        </Link>

        <div className="bg-card border border-border rounded-2xl p-5 sm:p-8">
          <h1 className="text-2xl sm:text-3xl font-heading font-bold text-center mb-2">
            Join Filmy
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground text-center mb-6 sm:mb-8">
            Create an account to save your preferences
          </p>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

            {/* First + Last Name */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>First Name</Label>
                <Input
                  {...form.register("firstname")}
                  placeholder="John"
                  className={form.formState.errors.firstname ? "border-red-500" : ""}
                />
                <p className="text-red-500 text-xs">
                  {form.formState.errors.firstname?.message}
                </p>
              </div>

              <div>
                <Label>Last Name</Label>
                <Input
                  {...form.register("lastname")}
                  placeholder="Doe"
                  className={form.formState.errors.lastname ? "border-red-500" : ""}
                />
                <p className="text-red-500 text-xs">
                  {form.formState.errors.lastname?.message}
                </p>
              </div>
            </div>

            {/* Email */}
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                {...form.register("email")}
                placeholder="you@example.com"
                className={form.formState.errors.email ? "border-red-500" : ""}
              />
              <p className="text-red-500 text-xs">
                {form.formState.errors.email?.message}
              </p>
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
              <p className="text-red-500 text-xs">
                {form.formState.errors.password?.message}
              </p>
            </div>

            <Button
              className="w-full gradient-cinematic glow-primary text-lg py-6 mt-6"
              disabled={loading}
            >
              {loading ? "Creating Account..." : "Sign Up"}
            </Button>

          </form>

          <div className="mt-6 text-center">
            <Link to="/login" className="text-sm text-muted-foreground hover:text-primary">
              Already have an account? Log in
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

export default Register;
