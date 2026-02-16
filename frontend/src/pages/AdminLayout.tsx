import { Outlet, Link, useNavigate, useLocation } from "react-router-dom";
import { authService } from "../services/auth";
import "./AdminLayout.css";

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    authService.clearToken();
    navigate("/admin");
  };

  const isActive = (path: string) => {
    return location.pathname === path ? "active" : "";
  };

  return (
    <div className="admin-layout">
      <nav className="admin-nav">
        <div className="nav-header">
          <h2>Admin Panel</h2>
        </div>
        
        <div className="nav-links">
          <Link to="/admin/calls" className={isActive("/admin/calls")}>
            Calls
          </Link>
          <Link to="/admin/stats" className={isActive("/admin/stats")}>
            Stats
          </Link>
          <Link to="/admin/settings" className={isActive("/admin/settings")}>
            Settings
          </Link>
        </div>

        <div className="nav-footer">
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>

      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  );
}
