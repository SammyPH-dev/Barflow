import Header from './Header'
import LoginCard from './LoginCard'
import ProfileSelection from './ProfileSelection'
import './App.css'


function App() {
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <ProfileSelection />
        <LoginCard />
      </main>
    </div> 
  )
}

export default App


