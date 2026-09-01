import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logo from "../logo.svg";
import "./Register.css";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");

  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();

    setError("");

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/register`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            email,
            password,
            phone,
            address,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.error);
        return;
      }

      // Account created.
      // Send user to login.
      navigate("/login");
    } catch (error) {
      setError("Unable to connect to server.");
    }
  };

  return (
    <div className="register-page">
      <div className="register-card">
        <div className="register-header">
          <img src={logo} alt="Job Manager logo" className="register-logo" />
          <h1 className="register-title">Create Account</h1>
        </div>

        <form onSubmit={handleRegister} className="register-form">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="register-input"
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="register-input"
          />

          <input
            type="text"
            placeholder="Phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="register-input"
          />

          <input
            type="text"
            placeholder="Address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="register-input"
          />

          <button type="submit" className="register-button">
            Create Account
          </button>
        </form>

        <button
          type="button"
          onClick={() => navigate("/login")}
          className="login-link-button"
        >
          Log in with email
        </button>

        {error && <p className="register-error">{error}</p>}
      </div>
    </div>
  );
}

export default Register;
