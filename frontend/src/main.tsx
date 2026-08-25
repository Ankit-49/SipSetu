import "./styles/index.css";
import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from "@sentry/react";
import "@/i18n"; // initialise i18n before rendering
import App from "./app/App";
import { AuthProvider } from './app/context/AuthContext'; 

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENVIRONMENT ?? "development",
    release: `sipsetu@${import.meta.env.VITE_APP_VERSION ?? "1.0.0"}`,
    tracesSampleRate: 0.1,
    integrations: [Sentry.browserTracingIntegration()],
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);