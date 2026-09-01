import { useEffect, useState } from "react";

function UserDashboard() {
  const [postings, setPostings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPostings = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/postings`,
        );

        if (!response.ok) {
          throw new Error("Failed to load postings");
        }

        const data = await response.json();
        setPostings(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadPostings();
  }, []);

  return (
    <div>
      <h1>User Dashboard</h1>
      {loading && <p>Loading postings...</p>}
      {error && <p>{error}</p>}
      {!loading && !error && postings.length === 0 && (
        <p>No postings available.</p>
      )}
      {!loading && !error && postings.length > 0 && (
        <ul>
          {postings.map((posting) => (
            <li key={posting.postingid}>
              <strong>{posting.company}</strong> - {posting.position}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default UserDashboard;
