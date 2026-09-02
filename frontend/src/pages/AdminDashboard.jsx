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
  const [expandedPostingId, setExpandedPostingId] = useState(null);
  const [applicants, setApplicants] = useState({});
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

  const toggleApplicants = async (postingId) => {
    if (expandedPostingId === postingId) {
      setExpandedPostingId(null);
      return;
    }

    setExpandedPostingId(postingId);
    setError("");

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/postings/${postingId}/applicants`,
      );
      const data = await response.json();
      if (!response.ok) {
        setError(data.error || "Failed to load applicants");
        return;
      }
      setApplicants((currentApplicants) => ({
        ...currentApplicants,
        [postingId]: data,
      }));
    } catch (err) {
      setError("Unable to load applicants.");
    }
  };

  const handleStatusChange = async (postingId, applicantId, status) => {
    setError("");

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/applications/postings/${postingId}/users/${applicantId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status }),
        },
      );
      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Failed to update application status");
        return;
      }

      setApplicants((currentApplicants) => ({
        ...currentApplicants,
        [postingId]: currentApplicants[postingId].map((applicant) =>
          applicant.user.userid === applicantId
            ? { ...applicant, status: data.status }
            : applicant,
        ),
      }));
    } catch (err) {
      setError("Unable to update application status.");
    }
  };

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
            <h2 className="my-postings-title">My Postings</h2>
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

          {!loading && postings.length === 0 && (
            <p>You have not added any postings yet.</p>
          )}
          {!loading && postings.length > 0 && (
            <ul className="admin-posting-list">
              {postings.map((posting) => (
                <li key={posting.postingid} className="admin-posting-item">
                  <button
                    type="button"
                    className="posting-accordion-button"
                    onClick={() => toggleApplicants(posting.postingid)}
                    aria-expanded={expandedPostingId === posting.postingid}
                  >
                    <span className="posting-accordion-title">
                      <strong>{posting.position}</strong>
                      <span>{posting.company}</span>
                      {posting.description && (
                        <small>{posting.description}</small>
                      )}
                    </span>
                    <span aria-hidden="true">
                      {expandedPostingId === posting.postingid ? "−" : "+"}
                    </span>
                  </button>

                  {expandedPostingId === posting.postingid && (
                    <div className="applicants-panel">
                      {applicants[posting.postingid] &&
                        applicants[posting.postingid].length === 0 && (
                          <p>No applicants yet.</p>
                        )}
                      {applicants[posting.postingid]?.map((applicant) => (
                        <div
                          key={applicant.user.userid}
                          className="applicant-row"
                        >
                          <div>
                            <strong>{applicant.user.email}</strong>
                            <span>
                              {applicant.user.phone || "No phone provided"}
                            </span>
                          </div>
                          <select
                            value={applicant.status}
                            onChange={(event) =>
                              handleStatusChange(
                                posting.postingid,
                                applicant.user.userid,
                                event.target.value,
                              )
                            }
                          >
                            <option value="Applied">Applied</option>
                            <option value="Interviewing">Interviewing</option>
                            <option value="Accepted">Accepted</option>
                            <option value="Rejected">Rejected</option>
                          </select>
                        </div>
                      ))}
                    </div>
                  )}
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
