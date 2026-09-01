import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import UserDashboard from "./pages/UserDashboard";
import AdminDashboard from "./pages/AdminDashboard";

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("jobmanager_user") || "null");
  } catch {
    return null;
  }
}

function ProtectedRoute({ children, allowedRole }) {
  const currentUser = getStoredUser();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && currentUser.usertype !== allowedRole) {
    return (
      <Navigate
        to={currentUser.usertype === "Admin" ? "/admin" : "/user"}
        replace
      />
    );
  }

  return children;
}

function LoginPage() {
  const currentUser = getStoredUser();

  if (currentUser) {
    return (
      <Navigate
        to={currentUser.usertype === "Admin" ? "/admin" : "/user"}
        replace
      />
    );
  }

  return <Login />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/user"
          element={
            <ProtectedRoute allowedRole="User">
              <UserDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRole="Admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
