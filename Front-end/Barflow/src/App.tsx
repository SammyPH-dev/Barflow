import Header from './Header'
import LoginCard from './LoginCard'
import ProfileSelection from './ProfileSelection'
// import {OrderCart} from './components/OrderCart'
// import type { CartItem } from './components/OrderCart'
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


