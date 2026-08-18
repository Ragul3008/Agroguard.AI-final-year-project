import { useState, useEffect } from "react";
import { getMyProfile, updateProfile } from "../../api.ts";
import { User, Phone, Mail, MapPin, Building, Map, Save, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { toast } from "sonner";

export function Profile() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    name: "",
    phone: "",
    email: "",
    village: "",
    district: "",
    state: "",
    auth_provider: "",
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const data = await getMyProfile();
      setProfile({
        name: data.name || "",
        phone: data.phone || "",
        email: data.email || "",
        village: data.village || "",
        district: data.district || "",
        state: data.state || "",
        auth_provider: data.auth_provider || "",
      });
    } catch (error) {
      console.error(error);
      toast.error("Failed to load profile details.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProfile(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const data = await updateProfile({
        name: profile.name,
        village: profile.village,
        district: profile.district,
        state: profile.state,
      });
      // Update local storage farmer data to reflect new name
      const userStr = localStorage.getItem("agroguard_user");
      if (userStr) {
        const user = JSON.parse(userStr);
        user.name = data.name;
        localStorage.setItem("agroguard_user", JSON.stringify(user));
      }
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error(error);
      toast.error("Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-green-600">
        <Loader2 className="w-10 h-10 animate-spin mb-4" />
        <p className="font-medium animate-pulse">Loading Profile...</p>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-2xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <User className="text-green-600 w-7 h-7" />
            My Profile
          </h1>
          <p className="text-sm text-gray-500 mt-1">Manage your account details and location</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-xl shadow-green-100/50 border border-green-50 mb-20 relative">
        {/* Decorative header background */}
        <div className="h-24 bg-gradient-to-r from-green-500 to-emerald-400 relative rounded-t-2xl">
          <div className="absolute -bottom-10 left-6 w-20 h-20 bg-white rounded-full p-1 shadow-md flex items-center justify-center">
            <div className="w-full h-full bg-green-50 rounded-full flex items-center justify-center border-2 border-dashed border-green-200">
              <User className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 pt-14 space-y-6">
          
          {/* Identity Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Identity</h3>
            
            <div className="space-y-2">
              <Label htmlFor="name" className="text-gray-700 flex items-center gap-2">
                <User className="w-4 h-4 text-green-500" /> Full Name
              </Label>
              <Input
                id="name"
                name="name"
                value={profile.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                className="focus-visible:ring-green-500 rounded-xl"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-gray-700 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" /> Email Address
                </Label>
                <Input
                  id="email"
                  value={profile.email || "Not provided"}
                  readOnly
                  className="bg-gray-50 text-gray-500 cursor-not-allowed rounded-xl border-gray-200"
                />
                {profile.auth_provider === "google" && (
                  <p className="text-xs text-blue-600 font-medium">Linked with Google</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone" className="text-gray-700 flex items-center gap-2">
                  <Phone className="w-4 h-4 text-gray-400" /> Phone Number
                </Label>
                <Input
                  id="phone"
                  value={profile.phone || "Not provided"}
                  readOnly
                  className="bg-gray-50 text-gray-500 cursor-not-allowed rounded-xl border-gray-200"
                />
                <p className="text-xs text-gray-400">Phone & Email cannot be edited directly.</p>
              </div>
            </div>
          </div>

          <div className="h-px bg-gray-100 my-6" />

          {/* Location Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Location Details</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="village" className="text-gray-700 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-green-500" /> Village / City
                </Label>
                <Input
                  id="village"
                  name="village"
                  value={profile.village}
                  onChange={handleChange}
                  placeholder="Enter your village or city"
                  className="focus-visible:ring-green-500 rounded-xl"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="district" className="text-gray-700 flex items-center gap-2">
                  <Building className="w-4 h-4 text-green-500" /> District
                </Label>
                <Input
                  id="district"
                  name="district"
                  value={profile.district}
                  onChange={handleChange}
                  placeholder="Enter your district"
                  className="focus-visible:ring-green-500 rounded-xl"
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="state" className="text-gray-700 flex items-center gap-2">
                  <Map className="w-4 h-4 text-green-500" /> State
                </Label>
                <Input
                  id="state"
                  name="state"
                  value={profile.state}
                  onChange={handleChange}
                  placeholder="Enter your state"
                  className="focus-visible:ring-green-500 rounded-xl"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 pb-8">
            <Button 
              type="submit" 
              disabled={saving}
              className="w-full bg-green-600 hover:bg-green-700 text-white rounded-xl py-6 shadow-lg shadow-green-600/20 transition-all hover:scale-[1.01] active:scale-[0.98] font-bold text-lg flex items-center gap-2"
            >
              {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
              {saving ? "Saving Changes..." : "Save Profile"}
            </Button>
          </div>

        </form>
      </div>
    </div>
  );
}
