import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./AdminDashboard.css";

function AdminDashboard() {
  const [postings, setPostings] = useState([]);
  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const currentUser = JSON.parse(
    localStorage.getItem("jobmanager_user") || "null",
  );
  const userId = currentUser?.userid;

  const loadPostings = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/postings`);
      if (!response.ok) throw new Error("Failed to load postings");
      const data = await response.json();
      setPostings(data.filter((posting) => posting.postedby === userId));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) loadPostings();
  }, [userId]);

  const handleCreatePosting = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/postings`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ company, position, description }),
        },
      );
      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Failed to create posting");
        return;
      }

      setPostings((currentPostings) => [...currentPostings, data]);
      setCompany("");
      setPosition("");
      setDescription("");
      setMessage("Posting added successfully");
    } catch (err) {
      setError("Unable to create posting.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-dashboard-page">
      <div className="admin-dashboard-card">
        <div className="admin-dashboard-header">
          <h1>Admin Dashboard</h1>
          <button
            type="button"
            className="logout-button-small"
            onClick={() => {
              localStorage.removeItem("jobmanager_user");
              navigate("/login", { replace: true });
            }}
          >
            Logout
          </button>
        </div>

        <section className="admin-section">
          <div className="admin-section-header">
            <h2>My Postings</h2>
            <button
              type="button"
              className="admin-refresh-button"
              onClick={loadPostings}
              disabled={loading}
              aria-label="Refresh postings"
              title="Refresh postings"
            >
              &#x21bb;
            </button>
          </div>

          {loading && <p>Loading postings...</p>}
          {!loading && postings.length === 0 && (
            <p>You have not added any postings yet.</p>
          )}
          {!loading && postings.length > 0 && (
            <ul className="admin-posting-list">
              {postings.map((posting) => (
                <li key={posting.postingid} className="admin-posting-item">
                  <strong>{posting.company}</strong>
                  <span>{posting.position}</span>
                  {posting.description && <p>{posting.description}</p>}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="admin-section">
          <h2>Add Posting</h2>
          <form className="posting-form" onSubmit={handleCreatePosting}>
            <input
              type="text"
              placeholder="Company"
              value={company}
              onChange={(event) => setCompany(event.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Position"
              value={position}
              onChange={(event) => setPosition(event.target.value)}
              required
            />
            <textarea
              placeholder="Description (optional)"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows="4"
            />
            <button type="submit" disabled={saving}>
              {saving ? "Adding..." : "Add Posting"}
            </button>
          </form>
        </section>

        {message && <p className="admin-success">{message}</p>}
        {error && <p className="admin-error">{error}</p>}
      </div>
    </div>
  );
}

export default AdminDashboard;
