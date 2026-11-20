import { useState } from 'react'
import './LoginCard.css'

export default function LoginCard() {
  const [showPassword, setShowPassword] = useState(false)

  return (
    <section className="login-card" aria-labelledby="login-title">
      <header className="login-card__header">
        <h1 id="login-title">Welcome back,</h1>
        <p>Enter your credentials to log in.</p>
      </header>

      <div className="login-form">
        <div className="login-form__field">
          <label htmlFor="login-username">Username</label>
          {/* htmlfor is the same as the for in html to link the label to the input field */}
          <input id="login-username" placeholder="Your username" />
        </div>

        <div className="login-form__field">
          <label htmlFor="login-password">Password</label>
          <div className="login-form__password">
            <input
              id="login-password"
              placeholder="Your password"
              type={showPassword ? 'text' : 'password'}
            />
            <button
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
              className="login-form__visibility"
              onClick={() => setShowPassword(!showPassword)}
              type="button"
            >
              <img src="/src/assets/eye.svg" alt="" />
            </button>
          </div>
        </div>

        <label className="login-form__remember">
          <input type="checkbox" defaultChecked />
          remember me
        </label>

        <button className="login-form__submit" type="button">
          connect
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M4 12h15m-6-6 6 6-6 6" />
          </svg>
        </button>
      </div>

      <p className="login-card__help">
        Forgot your password? <a href="mailto:responsable@barflow.fr">Contact your manager</a>
      </p>
    </section>
  )
}
