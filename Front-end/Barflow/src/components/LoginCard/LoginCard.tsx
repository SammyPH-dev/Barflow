import { useState, type FormEvent } from 'react'
import { login } from './services/auth' 
import './LoginCard.css'

type LoginCardProps = {
  username: string
  onUsernameChange: (newUsername: string) => void
  onConnect: (accessToken: string) => void
}

export default function LoginCard({ 
    username,
    onUsernameChange,
    onConnect 
  }: LoginCardProps) {
  const [errorMessage, setErrorMessage] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [password, setPassword] = useState('')

 async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try{
      const result = await login(username, password)
      onConnect(result.access_token)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Login failed')
    }
  }

  return (
    <section className="login-card" aria-labelledby="login-title">
      <header className="login-card__header">
        <h1 id="login-title">Welcome back,</h1>
        <p>Enter your credentials to log in.</p>
      </header>

      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-form__field">
          <label htmlFor="login-username">Email</label>
          {/* htmlfor is the same as the for in html to link the label to the input field */}
          <input id="login-username"
          value={username}
          onChange={(e) => onUsernameChange(e.target.value)}
          placeholder="Your email"
          required />
        </div>

        <div className="login-form__field">
          <label htmlFor="login-password">Password</label>
          <div className="login-form__password">
            <input
              id="login-password"
              placeholder="Your password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
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
          {errorMessage && <p role="alert">{errorMessage}</p>}
        <button className="login-form__submit" type="submit">
          connect
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M4 12h15m-6-6 6 6-6 6" />
          </svg>
        </button>
        
      </form>

      <p className="login-card__help">
        Forgot your password? <a href="mailto:responsable@barflow.fr">Click here to reset it</a>
      </p>
    </section>
  )
}
