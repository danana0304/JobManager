import { useNavigate } from "react-router-dom";
import "./AdminDashboard.css";

function AdminDashboard() {
  const navigate = useNavigate();

  return (
    <div className="admin-dashboard-page">
      <div className="admin-dashboard-card">
        <div className="admin-dashboard-header">
          <h1>Admin Dashboard</h1>
          <button
            type="button"
            className="logout-button"
            onClick={() => {
              localStorage.removeItem("jobmanager_user");
              navigate("/login", { replace: true });
            }}
          >
            Logout
          </button>
        </div>
        <p>Admin access has been granted.</p>
      </div>
    </div>
  );
}

export default AdminDashboard;
