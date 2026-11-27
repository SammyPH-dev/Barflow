import { useState } from 'react'
import Header from './Header'
import LoginCard from './LoginCard'
import ProfileSelection from './ProfileSelection'
import RecommendationsPage from './recommendations/RecommendationsPage'
import InventoryPage from './inventory/InventoryPage'
import BillsPage from './bills/BillsPage'
import DiscountsPage from './discounts/DiscountsPage'
import ActivityPage from './activity/ActivityPage'
import type { SidebarPage } from './navigation/Sidebar'
import './App.css'

export default function App() {
  // Temporary screen navigation only; this is not authentication.
  // While building, you can start with useState(true) to skip the login screen.
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const isConnected = accessToken !== null
  const [page, setPage] = useState<SidebarPage>('Sales')
  const [username, setUsername] = useState('Alex L.')


  // Picks the page to show. Every page gets the current page and the function to change it,
  // and passes them to its own Sidebar.
  function renderPage() {
    switch (page) {
      case 'Sales':
        return <RecommendationsPage activePage={page} onNavigate={setPage} />
      case 'Bills':
        return <BillsPage activePage={page} onNavigate={setPage} />
      case 'Inventory':
        return <InventoryPage activePage={page} onNavigate={setPage} />
      case 'Discounts':
        return <DiscountsPage activePage={page} onNavigate={setPage} />
      case 'Activity':
        return <ActivityPage activePage={page} onNavigate={setPage} />
    }
  }

  const headerLabel = !isConnected ? 'Login' : page === 'Sales' ? 'Recommendations' : page

  return (
    <div className="app-shell">
      <Header page={headerLabel} />
      {isConnected ? (
        renderPage()
      ) : (
        <main className="app-main">
          <ProfileSelection onSelectProfile={setUsername} />
          <LoginCard 
            username={username}
            onUsernameChange={setUsername}
            onConnect={setAccessToken} 
          />
        </main>
      )}
    </div>
  )
}
