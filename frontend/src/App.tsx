import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import './index.css'

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <h1>CyberAge V1</h1>
        <p>Auditable Autonomous Security-Testing Platform</p>
      </header>
      <main>
        <Dashboard />
      </main>
    </div>
  )
}

export default App
