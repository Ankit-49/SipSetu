import { RouterProvider } from 'react-router';
import { router } from './routes';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider } from '@/app/context/AuthContext';

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
      <Toaster position="bottom-right" closeButton />
    </AuthProvider>
  );
}