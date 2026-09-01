import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logo from "../logo.svg";
import "./Login.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/login`, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        credentials: "include",

        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error);
        return;
      }

      const userType = data.usertype ?? data.UserType ?? "User";
      localStorage.setItem(
        "jobmanager_user",
        JSON.stringify({
          userid: data.userid,
          email: data.email,
          usertype: userType,
        }),
      );

      if (userType === "Admin") {
        navigate("/admin");
      } else {
        navigate("/user");
      }
    } catch (error) {
      setError("Unable to connect to server.");
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <img src={logo} alt="Job Manager logo" className="login-logo" />
        <h1 className="login-title">Login</h1>

        <form onSubmit={handleLogin} className="login-form">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="login-input"
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="login-input"
          />

          <button type="submit" className="login-button">
            Login
          </button>
        </form>

        <button
          type="button"
          onClick={() => navigate("/register")}
          className="register-button"
        >
          Register
        </button>

        {error && <p className="login-error">{error}</p>}
      </div>
    </div>
  );
}

export default Login;
