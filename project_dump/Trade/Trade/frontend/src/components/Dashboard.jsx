import React, { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import './Dashboard.css'

const API_URL = 'http://localhost:8000/api'

export default function Dashboard({ onLogout }) {
  const { user, logout } = useAuth()
  const [bots, setBots] = useState([])
  const [selectedBot, setSelectedBot] = useState(null)
  const [showNewBotForm, setShowNewBotForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    strategy: 'ma_crossover',
    symbol: 'BTC/USDT',
    initialBalance: 10000,
    amountPerTrade: 100
  })

  useEffect(() => {
    // Load bots from localStorage (for now)
    const savedBots = localStorage.getItem('quantai_bots')
    if (savedBots) {
      setBots(JSON.parse(savedBots))
    }
  }, [])

  const handleCreateBot = () => {
    if (!formData.name) {
      alert('Please enter a bot name')
      return
    }

    const newBot = {
      id: Date.now(),
      ...formData,
      status: 'stopped',
      createdAt: new Date().toISOString(),
      pnl: 0,
      trades: 0,
      balance: formData.initialBalance
    }

    const updatedBots = [...bots, newBot]
    setBots(updatedBots)
    localStorage.setItem('quantai_bots', JSON.stringify(updatedBots))
    setShowNewBotForm(false)
    setFormData({
      name: '',
      strategy: 'ma_crossover',
      symbol: 'BTC/USDT',
      initialBalance: 10000,
      amountPerTrade: 100
    })
  }

  const handleStartBot = (botId) => {
    const updatedBots = bots.map(b =>
      b.id === botId ? { ...b, status: 'running' } : b
    )
    setBots(updatedBots)
    localStorage.setItem('quantai_bots', JSON.stringify(updatedBots))
  }

  const handleStopBot = (botId) => {
    const updatedBots = bots.map(b =>
      b.id === botId ? { ...b, status: 'stopped' } : b
    )
    setBots(updatedBots)
    localStorage.setItem('quantai_bots', JSON.stringify(updatedBots))
  }

  const handleLogout = () => {
    logout()
    onLogout()
  }

  return (
    <div className="dashboard">
      <nav className="dashboard-nav">
        <div className="nav-brand">⚡ AI Trading Bot</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ color: '#9aa4b2', fontSize: '14px' }}>
            {user?.full_name}
          </span>
          <button className="close-dashboard" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-header">
          <h2>Trading Bots</h2>
          <button
            className="btn-new-bot"
            onClick={() => setShowNewBotForm(!showNewBotForm)}
          >
            + Create Bot
          </button>
        </div>

        {showNewBotForm && (
          <div className="new-bot-form">
            <h3>Create New Trading Bot</h3>
            <div className="form-grid">
              <div>
                <label>Bot Name</label>
                <input
                  type="text"
                  placeholder="My Trading Bot"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
              </div>
              <div>
                <label>Strategy</label>
                <select
                  value={formData.strategy}
                  onChange={(e) =>
                    setFormData({ ...formData, strategy: e.target.value })
                  }
                >
                  <option value="ma_crossover">MA Crossover</option>
                  <option value="rsi">RSI</option>
                  <option value="ml">ML-Based</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>
              <div>
                <label>Trading Pair</label>
                <input
                  type="text"
                  placeholder="BTC/USDT"
                  value={formData.symbol}
                  onChange={(e) =>
                    setFormData({ ...formData, symbol: e.target.value })
                  }
                />
              </div>
              <div>
                <label>Initial Balance ($)</label>
                <input
                  type="number"
                  value={formData.initialBalance}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      initialBalance: parseFloat(e.target.value)
                    })
                  }
                />
              </div>
              <div>
                <label>Amount Per Trade ($)</label>
                <input
                  type="number"
                  value={formData.amountPerTrade}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      amountPerTrade: parseFloat(e.target.value)
                    })
                  }
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <button className="btn-primary" onClick={handleCreateBot}>
                Create Bot
              </button>
              <button
                className="btn-secondary"
                onClick={() => setShowNewBotForm(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {bots.length === 0 ? (
          <div className="empty-state">
            <p>No bots yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="bots-grid">
            {bots.map((bot) => (
              <div key={bot.id} className="bot-card">
                <div className="bot-header">
                  <h3>{bot.name}</h3>
                  <span className={`status ${bot.status}`}>{bot.status}</span>
                </div>
                <div className="bot-info">
                  <p>
                    <strong>Strategy:</strong> {bot.strategy}
                  </p>
                  <p>
                    <strong>Pair:</strong> {bot.symbol}
                  </p>
                  <p>
                    <strong>Balance:</strong> ${bot.balance.toFixed(2)}
                  </p>
                  <p>
                    <strong>P&L:</strong>{' '}
                    <span className={bot.pnl >= 0 ? 'profit' : 'loss'}>
                      ${bot.pnl.toFixed(2)}
                    </span>
                  </p>
                  <p>
                    <strong>Trades:</strong> {bot.trades}
                  </p>
                </div>
                <div className="bot-actions">
                  {bot.status === 'stopped' ? (
                    <button
                      className="btn-start"
                      onClick={() => handleStartBot(bot.id)}
                    >
                      Start
                    </button>
                  ) : (
                    <button
                      className="btn-stop"
                      onClick={() => handleStopBot(bot.id)}
                    >
                      Stop
                    </button>
                  )}
                  <button
                    className="btn-view"
                    onClick={() => setSelectedBot(bot)}
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedBot && (
        <div className="modal-overlay" onClick={() => setSelectedBot(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setSelectedBot(null)}
            >
              ✕
            </button>
            <h2>{selectedBot.name}</h2>
            <div className="modal-body">
              <p>
                <strong>Strategy:</strong> {selectedBot.strategy}
              </p>
              <p>
                <strong>Symbol:</strong> {selectedBot.symbol}
              </p>
              <p>
                <strong>Status:</strong> {selectedBot.status}
              </p>
              <p>
                <strong>Current Balance:</strong> ${selectedBot.balance.toFixed(2)}
              </p>
              <p>
                <strong>Total P&L:</strong>{' '}
                <span className={selectedBot.pnl >= 0 ? 'profit' : 'loss'}>
                  ${selectedBot.pnl.toFixed(2)}
                </span>
              </p>
              <p>
                <strong>Total Trades:</strong> {selectedBot.trades}
              </p>
              <p>
                <strong>Created:</strong>{' '}
                {new Date(selectedBot.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
