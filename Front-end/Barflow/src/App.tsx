import Header from './Header'
import LoginCard from './LoginCard'
import ProfileSelection from './ProfileSelection'
import {OrderCart} from './components/OrderCart'
import type { CartItem } from './components/OrderCart'
import './App.css'



function App() {

//  const items: CartItem[] = [
//     {
//       id: '1',
//       name: 'Negroni',
//       description: 'Gin, vermouth, Campari',
//       quantity: 1,
//       unitPrice: 12,
//     },
//   ]
  
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <ProfileSelection />
        <LoginCard />
        {/* <OrderCart
          orderNumber="ORD-001"
          openedAt="9:45 AM"
          tableName="Table 1"
          serverName="Sam"
          guestCount={2}
          taxRate={0.15}
          items={items}
          activeOrders={[]}
          onUpdateQuantity={(itemId, newQuantity) => {
              console.log(itemId, newQuantity) // Replace with state update logic
        }}/> */}
      </main>
    </div> 
  )
}

export default App


