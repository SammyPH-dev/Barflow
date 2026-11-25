import { useState } from 'react'
import Header from './Header'
import LoginCard from './LoginCard'
import ProfileSelection from './ProfileSelection'
import RecommendationsPage from './recommendations/RecommendationsPage'
import './App.css'

export default function App() {
  // Temporary screen navigation only; this is not authentication.
  const [showRecommendations, setShowRecommendations] = useState(false)

  // Passed to LoginCard so its connect button can change the screen.
  function openRecommendations() {
    setShowRecommendations(true)
  }

  return (
    <div className="app-shell">
      <Header page={showRecommendations ? 'Recommandations' : 'Login'} />
      {showRecommendations ? (
        <RecommendationsPage />
      ) : (
        <main className="app-main">
          <ProfileSelection />
          <LoginCard onConnect={openRecommendations} />
        </main>
      )}
    </div>
  )
}
