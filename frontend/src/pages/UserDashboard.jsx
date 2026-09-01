import { useEffect, useState } from "react";
import "./UserDashboard.css";

function UserDashboard() {
  const [activeTab, setActiveTab] = useState("available"); // "available" or "applications"
  const [availablePostings, setAvailablePostings] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [allPostings, setAllPostings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const currentUser = JSON.parse(
    localStorage.getItem("jobmanager_user") || "null",
  );
  const userId = currentUser?.userid;
  const userName = currentUser?.email?.split("@")[0] || "User";

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError("");
      try {
        // Fetch all postings
        const postingsRes = await fetch(
          `${process.env.REACT_APP_API_URL}/postings`,
        );
        if (!postingsRes.ok) throw new Error("Failed to load postings");
        const postingsData = await postingsRes.json();
        setAllPostings(postingsData);

        // Fetch available postings (not yet applied)
        const availableRes = await fetch(
          `${process.env.REACT_APP_API_URL}/postings/not-applied/${userId}`,
        );
        if (!availableRes.ok)
          throw new Error("Failed to load available postings");
        const availableData = await availableRes.json();
        setAvailablePostings(availableData);

        // Fetch user's applications
        const applicationsRes = await fetch(
          `${process.env.REACT_APP_API_URL}/applications/${userId}`,
        );
        if (!applicationsRes.ok) throw new Error("Failed to load applications");
        const applicationsData = await applicationsRes.json();
        setMyApplications(applicationsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadData();
    }
  }, [userId]);

  const handleLogout = () => {
    localStorage.removeItem("jobmanager_user");
    window.location.href = "/login";
  };

  const handleApply = (postingId) => {
    console.log(`Apply clicked for posting ${postingId}`);
    // TODO: Implement apply functionality
  };

  const getPostingDetails = (postingId) => {
    return allPostings.find((p) => p.postingid === postingId);
  };

  return (
    <div className="user-dashboard-page">
      <div className="user-dashboard-container">
        <div className="user-dashboard-header">
          <h1>Welcome {userName}</h1>
          <button
            type="button"
            className="logout-button-small"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>

        <div className="dashboard-tabs">
          <button
            className={`tab-button ${activeTab === "available" ? "active" : ""}`}
            onClick={() => setActiveTab("available")}
          >
            Available Postings
          </button>
          <button
            className={`tab-button ${activeTab === "applications" ? "active" : ""}`}
            onClick={() => setActiveTab("applications")}
          >
            My Applications
          </button>
        </div>

        {loading && <p className="user-dashboard-loading">Loading data...</p>}
        {error && <p className="user-dashboard-error">{error}</p>}

        {!loading && !error && activeTab === "available" && (
          <>
            {availablePostings.length === 0 ? (
              <p className="user-dashboard-empty">
                No available postings at this time.
              </p>
            ) : (
              <ul className="user-dashboard-list">
                {availablePostings.map((posting) => (
                  <li key={posting.postingid} className="user-dashboard-item">
                    <div className="posting-content">
                      <strong>{posting.company}</strong>
                      <span>{posting.position}</span>
                    </div>
                    <button
                      className="apply-button"
                      onClick={() => handleApply(posting.postingid)}
                    >
                      Apply
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {!loading && !error && activeTab === "applications" && (
          <>
            {myApplications.length === 0 ? (
              <p className="user-dashboard-empty">
                You haven't applied for any postings yet.
              </p>
            ) : (
              <ul className="user-dashboard-list">
                {myApplications.map((app) => {
                  const posting = getPostingDetails(app.postingid);
                  return (
                    <li
                      key={app.postingid}
                      className="user-dashboard-item application-item"
                    >
                      <div className="posting-content">
                        <strong>
                          {posting
                            ? posting.company
                            : `Posting #${app.postingid}`}
                        </strong>
                        <span>
                          {posting ? posting.position : "Unknown position"}
                        </span>
                      </div>
                      <div className="application-status">
                        <span className={`status ${app.status.toLowerCase()}`}>
                          {app.status}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default UserDashboard;
