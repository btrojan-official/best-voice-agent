import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { authService } from "./services/auth";
import Chat from "./pages/Chat";
import AdminLogin from "./pages/AdminLogin";
import AdminLayout from "./pages/AdminLayout";
import AdminCalls from "./pages/AdminCalls";
import CallDetails from "./pages/CallDetails";
import AdminStats from "./pages/AdminStats";
import AdminSettings from "./pages/AdminSettings";
import "./App.css";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/admin" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<Chat />} />
        
        <Route path="/admin" element={<AdminLogin />} />
        
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route path="calls" element={<AdminCalls />} />
          <Route path="calls/:callId" element={<CallDetails />} />
          <Route path="stats" element={<AdminStats />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
