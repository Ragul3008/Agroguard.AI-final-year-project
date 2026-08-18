import { Outlet, useNavigate, useLocation } from "react-router";
import { useEffect, useState } from "react";
import { Home, History, Info, User, LogOut } from "lucide-react";
import { Toaster } from "./ui/sonner";

export function Root() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem("agroguard_user");
    setIsLoggedIn(!!user);

    // Redirect to login if not logged in and not on login page
    if (!user && location.pathname !== "/") {
      navigate("/");
    }
    // navigate is intentionally omitted — it is a stable reference per React Router
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem("agroguard_user");
    setIsLoggedIn(false);
    navigate("/");
  };

  const navItems = [
    { path: "/chat", icon: Home, label: "Chat" },
    { path: "/history", icon: History, label: "History" },
    { path: "/about", icon: Info, label: "About" },
    { path: "/profile", icon: User, label: "Profile" },
  ];

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-green-50 to-emerald-50">
      <Toaster position="top-center" richColors />
      {/* Header */}
      {isLoggedIn && location.pathname !== "/" && (
        <header className="bg-green-600 text-white px-4 py-3 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2">
            <img
              src="/logo.png"
              alt="AgroGuard AI"
              className="w-10 h-10 rounded-full object-cover shadow-sm bg-white p-0.5"
            />
            <div>
              <h1 className="font-bold text-lg">AgroGuard.ai</h1>
              <p className="text-xs text-green-100">Crop Disease Detection</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 hover:bg-green-700 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </header>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      {/* Bottom Navigation */}
      {isLoggedIn && location.pathname !== "/" && (
        <nav className="bg-white border-t border-gray-200 px-2 py-2 shadow-lg">
          <div className="flex justify-around items-center max-w-md mx-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? "text-green-600 bg-green-50"
                      : "text-gray-600 hover:text-green-600 hover:bg-green-50"
                  }`}
                >
                  <Icon className="w-6 h-6" />
                  <span className="text-xs font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}