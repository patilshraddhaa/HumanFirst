import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/AuthContext";
import { LandingPage } from "./routes/landing/LandingPage";
import { LoginPage } from "./routes/landing/LoginPage";
import { DashboardPage } from "./routes/dashboard/DashboardPage";
import {
  DraftEditorPage,
} from "./features/draft-flow";
import { DraftPreviewPage } from "./routes/drafts/preview/DraftPreviewPage";
import { MCPSetupPage } from "./routes/drafts/setup/MCPSetupPage";
import { PublicReadPage } from "./routes/posts/read/PublicReadPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isBootstrapping, user } = useAuth();
  if (isBootstrapping) return null;
  if (!user) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/p/:slug" element={<PublicReadPage />} />

      {/* Authenticated */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/drafts/:draftId/edit"
        element={
          <ProtectedRoute>
            <DraftEditorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/drafts/:draftId/setup"
        element={
          <ProtectedRoute>
            <MCPSetupPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/drafts/:draftId/preview"
        element={
          <ProtectedRoute>
            <DraftPreviewPage />
          </ProtectedRoute>
        }
      />

      {/* Retired standalone prototype */}
      <Route path="/editor" element={<Navigate to="/dashboard" replace />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
