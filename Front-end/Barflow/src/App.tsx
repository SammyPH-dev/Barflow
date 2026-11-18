import Header from './Header'
import LoginCard from './LoginCard'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <LoginCard />
      </main>
    </div> 
  )
}

export default App


