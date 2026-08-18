import { useState } from "react";
import { forgotPassword, resetPassword, login } from "../../api.ts";
import { useNavigate } from "react-router";
import { Mail, Lock, Eye, EyeOff, ArrowLeft, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { toast } from "sonner";

type ForgotPasswordStep = "email" | "otp" | "new-password";

export function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<ForgotPasswordStep>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [otpDigits, setOtpDigits] = useState<string[]>(["", "", "", "", "", ""]);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please enter your email address");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const data = await forgotPassword(email);
      toast.success("If an account exists, an OTP has been sent to your email");
      setStep("otp");
      setOtpDigits(["", "", "", "", "", ""]);
    } catch (err) {
      setError("Failed to send OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value) || value.length > 1) return;
    const newDigits = [...otpDigits];
    newDigits[index] = value;
    setOtpDigits(newDigits);
    if (value && index < 5) {
      // Auto-focus next input
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
    const combined = newDigits.join("");
    setOtp(combined);
    if (combined.length === 6) {
      setError("");
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    const digits = pasted.split("");
    setOtpDigits(digits.map((d, i) => d || ""));
    setOtp(pasted);
    // Focus the next empty input
    const nextEmpty = digits.findIndex((d, i) => !d);
    if (nextEmpty >= 0) {
      document.getElementById(`otp-${nextEmpty}`)?.focus();
    } else if (digits.length === 6) {
      setError("");
    }
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== 6) {
      setError("Please enter the 6-digit OTP");
      return;
    }
    try {
      setLoading(true);
      setError("");
      // Just verify OTP by attempting to reset with a dummy password
      // We'll actually do the reset in the next step
      setStep("new-password");
    } catch (err) {
      setError("Invalid or expired OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || !confirmPassword) {
      setError("Please fill in both password fields");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const data = await resetPassword(email, otp, password);
      if (data.access_token) {
        localStorage.setItem("agroguard_token", data.access_token);
        localStorage.setItem("agroguard_refresh_token", data.refresh_token);
        localStorage.setItem("agroguard_user", JSON.stringify({
          email: data.farmer.email,
          name: data.farmer.name,
          joinedDate: new Date().toISOString(),
        }));
        toast.success("Password reset successful!");
        navigate("/chat");
      } else {
        setError(data.message || "Password reset failed. Please try again.");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Password reset failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    if (step === "otp") {
      setStep("email");
      setOtp("");
      setOtpDigits(["", "", "", "", "", ""]);
    } else if (step === "new-password") {
      setStep("otp");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <button onClick={() => navigate("/")} className="absolute left-0 top-0 text-gray-400 hover:text-gray-600">
            <ArrowLeft className="w-6 h-6" />
          </button>
          <img
            src="/logo.png"
            alt="AgroGuard AI Logo"
            className="w-24 h-24 rounded-2xl object-cover shadow-lg mx-auto mb-4 bg-white p-1"
          />
          <h1 className="text-3xl font-bold text-green-800 mb-2">AgroGuard.ai</h1>
          <p className="text-gray-600">Reset Your Password</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6 space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800">
              {step === "email" ? "Enter Your Email" : step === "otp" ? "Enter OTP" : "New Password"}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {step === "email" && "We'll send a 6-digit OTP to your registered email"}
              {step === "otp" && "Enter the 6-digit code sent to your email"}
              {step === "new-password" && "Choose a new password for your account"}
            </p>
          </div>

          {step === "email" && (
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input id="email" type="email"
                    placeholder="your@email.com"
                    value={email} onChange={(e) => setEmail(e.target.value)} className="pl-10" />
                </div>
              </div>

              {error && <p className="text-red-500 text-sm text-center flex items-center justify-center gap-1">
                <AlertCircle className="w-4 h-4" /> {error}
              </p>}

              <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 text-white" disabled={loading}>
                {loading ? "Sending..." : "Send OTP"}
              </Button>
            </form>
          )}

          {step === "otp" && (
            <form onSubmit={handleOtpSubmit} className="space-y-4">
              <div className="flex gap-2 justify-center">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Input
                    key={i}
                    id={`otp-${i}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={otpDigits[i]}
                    onChange={(e) => handleOtpChange(i, e.target.value)}
                    onPaste={handleOtpPaste}
                    onKeyDown={(e) => {
                      if (e.key === "Backspace" && !otpDigits[i] && i > 0) {
                        document.getElementById(`otp-${i - 1}`)?.focus();
                      }
                    }}
                    className="w-12 h-14 text-center text-2xl font-bold"
                    autoComplete="one-time-code"
                    autoFocus={i === 0}
                  />
                ))}
              </div>

              {error && <p className="text-red-500 text-sm text-center flex items-center justify-center gap-1">
                <AlertCircle className="w-4 h-4" /> {error}
              </p>}

              <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 text-white" disabled={loading || otp.length !== 6}>
                {loading ? "Verifying..." : "Verify OTP"}
              </Button>
            </form>
          )}

          {step === "new-password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">New Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input id="password" type={showPassword ? "text" : "password"}
                    placeholder="••••••••" value={password}
                    onChange={(e) => setPassword(e.target.value)} className="pl-10 pr-10" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input id="confirmPassword" type={showPassword ? "text" : "password"}
                    placeholder="••••••••" value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)} className="pl-10" />
                </div>
              </div>

              {error && <p className="text-red-500 text-sm text-center flex items-center justify-center gap-1">
                <AlertCircle className="w-4 h-4" /> {error}
              </p>}

              <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 text-white" disabled={loading}>
                {loading ? "Resetting..." : "Reset Password"}
              </Button>
            </form>
          )}

          <div className="text-center">
            <button onClick={goBack}
              className="text-sm text-green-600 hover:text-green-700 font-medium flex items-center justify-center gap-1 mx-auto">
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-white/50 rounded-lg p-3">
            <div className="text-2xl mb-1">🌱</div>
            <p className="text-xs text-gray-600">Disease Detection</p>
          </div>
          <div className="bg-white/50 rounded-lg p-3">
            <div className="text-2xl mb-1">🔍</div>
            <p className="text-xs text-gray-600">AI Analysis</p>
          </div>
          <div className="bg-white/50 rounded-lg p-3">
            <div className="text-2xl mb-1">💊</div>
            <p className="text-xs text-gray-600">Solutions</p>
          </div>
        </div>
      </div>
    </div>
  );
}