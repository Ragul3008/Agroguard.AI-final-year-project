import { RouterProvider } from 'react-router';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { router } from './routes.tsx';

export default function App() {
  const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID as string | undefined;

  if (!clientId) {
    return <RouterProvider router={router} />;
  }

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <RouterProvider router={router} />
    </GoogleOAuthProvider>
  );
}
