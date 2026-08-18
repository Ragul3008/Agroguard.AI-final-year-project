import { createBrowserRouter } from "react-router";
import { lazy, Suspense } from "react";
import { Root } from "./components/Root";

const Login = lazy(() => import("./components/Login").then(m => ({ default: m.Login })));
const ForgotPassword = lazy(() => import("./components/ForgotPassword").then(m => ({ default: m.ForgotPassword })));
const Chat = lazy(() => import("./components/Chat").then(m => ({ default: m.Chat })));
const History = lazy(() => import("./components/History").then(m => ({ default: m.History })));
const About = lazy(() => import("./components/About").then(m => ({ default: m.About })));
const Developer = lazy(() => import("./components/Developer").then(m => ({ default: m.Developer })));
const Profile = lazy(() => import("./components/Profile").then(m => ({ default: m.Profile })));

const Fallback = () => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
    <div style={{ width: 32, height: 32, border: "3px solid #16a34a", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, element: <Suspense fallback={<Fallback />}><Login /></Suspense> },
      { path: "forgot-password", element: <Suspense fallback={<Fallback />}><ForgotPassword /></Suspense> },
      { path: "chat", element: <Suspense fallback={<Fallback />}><Chat /></Suspense> },
      { path: "history", element: <Suspense fallback={<Fallback />}><History /></Suspense> },
      { path: "about", element: <Suspense fallback={<Fallback />}><About /></Suspense> },
      { path: "developer", element: <Suspense fallback={<Fallback />}><Developer /></Suspense> },
      { path: "profile", element: <Suspense fallback={<Fallback />}><Profile /></Suspense> },
    ],
  },
]);
