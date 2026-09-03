import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAuditLog } from "../utils/audit";
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
  const [editingPostingId, setEditingPostingId] = useState(null);
  const navigate = useNavigate();
  const currentUser = JSON.parse(
    localStorage.getItem("jobmanager_user") || "null",
  );
  const userId = currentUser?.userid;
  const userName = currentUser?.email?.split("@")[0] || "User";

  const loadPostings = useCallback(async () => {
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
  }, [userId]);

  useEffect(() => {
    if (userId) loadPostings();
  }, [loadPostings, userId]);

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
      await createAuditLog({
        action: "UPDATE",
        entityType: "Application",
        actorUserId: userId,
        entityId: applicantId,
        newValues: {
          postingid: postingId,
          userid: applicantId,
          status: data.status,
        },
      });
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
      const isEditing = editingPostingId !== null;
      const endpoint = isEditing
        ? `${process.env.REACT_APP_API_URL}/postings/${editingPostingId}`
        : `${process.env.REACT_APP_API_URL}/postings`;
      const response = await fetch(endpoint, {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          company,
          position,
          description,
          ...(isEditing ? {} : { postedby: userId }),
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Failed to create posting");
        return;
      }

      setPostings((currentPostings) =>
        isEditing
          ? currentPostings.map((posting) =>
              posting.postingid === editingPostingId ? data : posting,
            )
          : [...currentPostings, data],
      );
      await createAuditLog({
        action: isEditing ? "UPDATE" : "CREATE",
        entityType: "Posting",
        actorUserId: userId,
        entityId: data.postingid,
        newValues: data,
      });
      setEditingPostingId(null);
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

  const startEditingPosting = (posting) => {
    setEditingPostingId(posting.postingid);
    setCompany(posting.company);
    setPosition(posting.position);
    setDescription(posting.description || "");
    setMessage("");
    setError("");
  };

  const handleDeletePosting = async (postingId) => {
    setError("");
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/postings/${postingId}`,
        { method: "DELETE", credentials: "include" },
      );
      const data = await response.json();
      if (!response.ok) {
        setError(data.error || "Failed to delete posting");
        return;
      }
      setPostings((currentPostings) =>
        currentPostings.filter((posting) => posting.postingid !== postingId),
      );
      setExpandedPostingId(null);
      await createAuditLog({
        action: "DELETE",
        entityType: "Posting",
        actorUserId: userId,
        entityId: postingId,
      });
    } catch (err) {
      setError("Unable to delete posting.");
    }
  };

  return (
    <div className="admin-dashboard-page">
      <div className="admin-dashboard-card">
        <div className="admin-dashboard-header">
          <h1>Job Postings for {userName}</h1>
          <button
            type="button"
            className="logout-button-small"
            onClick={async () => {
              await createAuditLog({
                action: "LOGOUT",
                entityType: "User",
                actorUserId: userId,
                entityId: userId,
              });
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
                  <div className="posting-actions">
                    <button
                      type="button"
                      onClick={() => startEditingPosting(posting)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeletePosting(posting.postingid)}
                    >
                      Delete
                    </button>
                  </div>

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
                            <span>{applicant.user.email}</span>
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
          <h2>{editingPostingId === null ? "Add Posting" : "Edit Posting"}</h2>
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
              {saving
                ? editingPostingId === null
                  ? "Adding..."
                  : "Saving..."
                : editingPostingId === null
                  ? "Add Posting"
                  : "Save Posting"}
            </button>
            {editingPostingId !== null && (
              <button
                type="button"
                className="cancel-edit-button"
                onClick={() => {
                  setEditingPostingId(null);
                  setCompany("");
                  setPosition("");
                  setDescription("");
                }}
              >
                Cancel
              </button>
            )}
          </form>
        </section>

        {message && <p className="admin-success">{message}</p>}
        {error && <p className="admin-error">{error}</p>}
      </div>
    </div>
  );
}

export default AdminDashboard;
