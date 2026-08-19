import { useState, useEffect } from "react";
import { login, register, googleLogin } from "../../api.ts";
import { useNavigate, Link } from "react-router";
import { GoogleLogin } from "@react-oauth/google";
import { Sprout, Mail, Lock, Eye, EyeOff, User, Phone, MapPin, Chrome } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { toast } from "sonner";
import logoImg from "../../assets/logo.png";

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [village, setVillage] = useState("");
  const [district, setDistrict] = useState("");
  const [state, setState] = useState("");
  const [googleClientId, setGoogleClientId] = useState("");

  // Load Google Client ID from env
  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID;
    if (clientId) {
      setGoogleClientId(clientId);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      alert("Please fill in all fields");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const data = isSignUp
        ? await register(name, phone, email, password, village, district, state)
        : await login(email, password);
      if (data.access_token) {
        localStorage.setItem("agroguard_token", data.access_token);
        localStorage.setItem("agroguard_refresh_token", data.refresh_token);
        localStorage.setItem("agroguard_user", JSON.stringify({
          email,
          name: name || email.split("@")[0],
          joinedDate: new Date().toISOString(),
        }));
        navigate("/chat");
      } else {
        setError(
          data.message ||
          (Array.isArray(data.detail)
            ? data.detail.map((e: any) => e.msg).join(", ")
            : data.detail) ||
          "Login failed. Try again."
        );
      }
    } catch (err) {
      setError("Cannot connect to server. Is backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      setLoading(true);
      setError("");
      const data = await googleLogin(credentialResponse.credential);
      if (data.access_token) {
        localStorage.setItem("agroguard_token", data.access_token);
        localStorage.setItem("agroguard_refresh_token", data.refresh_token);
        localStorage.setItem("agroguard_user", JSON.stringify({
          email: data.farmer.email,
          name: data.farmer.name,
          joinedDate: new Date().toISOString(),
        }));
        toast.success(`Welcome, ${data.farmer.name}!`);
        navigate("/chat");
      } else {
        setError(data.message || "Google login failed. Try again.");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Google login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError("Google sign-in was cancelled or failed.");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img
            src={logoImg}
            alt="AgroGuard AI Logo"
            className="w-24 h-24 rounded-2xl object-cover shadow-lg mx-auto mb-4 bg-white p-1"
          />
          <h1 className="text-3xl font-bold text-green-800 mb-2">AgroGuard.ai</h1>
          <p className="text-gray-600">Your AI-Powered Crop Health Assistant</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6 space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800">
              {isSignUp ? "Create Account" : "Welcome Back"}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {isSignUp ? "Sign up to start monitoring your crops" : "Sign in to continue crop monitoring"}
            </p>
          </div>

          {/* Google Sign-In Button */}
          {googleClientId && (
            <div className="flex justify-center w-full">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap={false}
                autoSelect={false}
                shape="rectangular"
                width="100%"
                logo_alignment="center"
              />
            </div>
          )}

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">Or continue with email/phone</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Signup Only Fields */}
            {isSignUp && (
              <>
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="Your full name" value={name}
                      onChange={(e) => setName(e.target.value)} className="pl-10" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="9876543210" value={phone}
                      onChange={(e) => setPhone(e.target.value)} className="pl-10" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Village</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="Your village" value={village}
                      onChange={(e) => setVillage(e.target.value)} className="pl-10" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>District</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="Your district" value={district}
                      onChange={(e) => setDistrict(e.target.value)} className="pl-10" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>State</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="Your state" value={state}
                      onChange={(e) => setState(e.target.value)} className="pl-10" />
                  </div>
                </div>
              </>
            )}

            {/* Email or Phone */}
            <div className="space-y-2">
              <Label htmlFor="email">Email or Phone Number</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input id="email" type="text"
                  placeholder="Email or 10-digit phone number"
                  value={email} onChange={(e) => setEmail(e.target.value)} className="pl-10" />
              </div>
            </div>

            {/* Password */}
            {!isSignUp && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
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

                <div className="text-right">
                  <Link to="/forgot-password" className="text-sm text-green-600 hover:text-green-700 font-medium">
                    Forgot password?
                  </Link>
                </div>
              </>
            )}

            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
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
            )}

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}

            <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 text-white" disabled={loading}>
              {loading ? "Please wait..." : isSignUp ? "Sign Up" : "Sign In"}
            </Button>
          </form>

          <div className="text-center">
            <button onClick={() => setIsSignUp(!isSignUp)}
              className="text-sm text-green-600 hover:text-green-700 font-medium">
              {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
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