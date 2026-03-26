import React, { useState } from 'react'
import { AuthProvider, useAuth } from './AuthContext'
import SignUp from './components/SignUp'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import './App.css'

function AppContent() {
  const [currentPage, setCurrentPage] = useState('landing')
  const { user, loading } = useAuth()

  // If loading auth state, show nothing
  if (loading) {
    return <div style={{ background: '#050d18', minHeight: '100vh' }} />
  }

  // If user is logged in, always show dashboard
  if (user) {
    return <Dashboard onLogout={() => setCurrentPage('landing')} />
  }

  // Show auth or landing pages
  if (currentPage === 'signup') {
    return <SignUp onNavigate={setCurrentPage} />
  }

  if (currentPage === 'login') {
    return <Login onNavigate={setCurrentPage} />
  }

  return <Landing onNavigate={setCurrentPage} />
}

function Landing({ onNavigate }) {
  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">QuantAI</span>
          </div>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#testimonials">Testimonials</a>
          </div>
          <div className="nav-buttons">
            <button className="btn-login" onClick={() => onNavigate('login')}>Log In</button>
            <button className="btn-started" onClick={() => onNavigate('signup')}>Get Started</button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-background"></div>
        <div className="hero-content">
          <div className="beta-badge">
            <span className="beta-dot">●</span>
            Now in Public Beta
          </div>
          <h1 className="hero-title">
            Paper Trade Smarter with<br />
            <span className="highlight">AI-Powered Intelligence</span>
          </h1>
          <p className="hero-subtitle">
            Test strategies, analyze performance, and automate decision-making<br />
            with a real institutional-grade AI trading engine. No risk, pure alpha.
          </p>
          <div className="hero-buttons">
            <button className="btn-primary" onClick={() => onNavigate('signup')}>
              Get Started Free <span className="arrow">→</span>
            </button>
            <button className="btn-secondary">View Demo</button>
          </div>
        </div>
        <div className="made-with">
          <span className="replit-badge">
            <span className="replit-icon">⚙</span>
            Made with Replit
            <span className="close-x">×</span>
          </span>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="tech-stack">
        <div className="tech-label">BUILT WITH MODERN FINANCIAL INFRASTRUCTURE</div>
        <div className="tech-items">
          <div className="tech-item">⚡ FastAPI</div>
          <div className="tech-item">▶ Python ML</div>
          <div className="tech-item">⭘ SQLAlchemy</div>
          <div className="tech-item">⚙ React</div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" id="features">
        <h2 className="section-title">Institutional-Grade Tools</h2>
        <p className="section-subtitle">Stop guessing. Start engineering your edge with tools designed for quantitative analysis.</p>
        
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🧠</div>
            <h3>AI Strategy Engine</h3>
            <p>Our ML pipelines analyze market structure, volatility, and volume anomalies to generate high-confidence signals.</p>
          </div>
          
          <div className="feature-card featured">
            <div className="feature-icon">▶</div>
            <h3>Paper Trading Simulator</h3>
            <p>Test your execution with realistic slippage and fee modeling before risking a single satoshi.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Real-Time Metrics</h3>
            <p>Monitor equity curves, drawdown, Sharpe ratio, and exposure in real-time with sub-second latency.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">⏱</div>
            <h3>Backtesting Engine</h3>
            <p>Run historical simulations across terabytes of market data to validate your thesis instantly.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Telegram Alerts</h3>
            <p>Get instant notifications for every buy/sell decision, risk event, and daily performance summary.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🛡</div>
            <h3>Risk Management</h3>
            <p>Hard-coded risk caps, position sizing rules, and automated stop-losses to protect your capital.</p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <h2 className="section-title">How It Works</h2>
        
        <div className="how-grid">
          <div className="how-left">
            <div className="step">
              <div className="step-number">01</div>
              <h3>Connect Data</h3>
              <p>Select your exchange pairs and timeframe. We handle the websocket ingestion and normalization.</p>
            </div>
            
            <div className="step">
              <div className="step-number">02</div>
              <h3>Run AI Strategies</h3>
              <p>Activate pre-trained models or configure your own parameters. The bot runs 24/7 autonomously.</p>
            </div>
            
            <div className="step">
              <div className="step-number">03</div>
              <h3>Analyze Results</h3>
              <p>Deep dive into every decision. See exactly why the AI took a trade and track performance.</p>
            </div>
          </div>
          
          <div className="how-right">
            <div className="decision-log">
              <div className="log-header">
                <span>DECISION LOG</span>
                <span className="live-badge">LIVE</span>
              </div>
              <div className="log-entry">
                <div className="log-symbol">BUY BTC-USD</div>
                <div className="log-confidence">0.92 CONFIDENCE</div>
                <div className="log-reason">Reason: RSI Divergence + Volatility Breakout</div>
                <div className="log-model">Model: v2.4.1 (Transformer)</div>
              </div>
              <div className="log-entry">
                <div className="log-symbol">SELL ETH-USD</div>
                <div className="log-confidence">0.88 CONFIDENCE</div>
                <div className="log-reason">Reason: Resistance Rejection</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials" id="testimonials">
        <h2 className="section-title">Trusted by Traders</h2>
        
        <div className="testimonials-grid">
          <div className="testimonial">
            <p>"This feels like a real trading terminal. I finally understand what my strategies are doing."</p>
            <div className="testimonial-author">
              <div className="author-name">Alex R.</div>
              <div className="author-title">Quant Researcher</div>
            </div>
          </div>
          
          <div className="testimonial">
            <p>"The paper trading mode saved me from losing real money while learning. Essential tool."</p>
            <div className="testimonial-author">
              <div className="author-name">Jordan K.</div>
              <div className="author-title">Crypto Enthusiast</div>
            </div>
          </div>
          
          <div className="testimonial">
            <p>"Best analytics dashboard I've used for crypto testing. The Telegram alerts alone are worth it."</p>
            <div className="testimonial-author">
              <div className="author-name">Sam T.</div>
              <div className="author-title">Day Trader</div>
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="disclaimer">
        <p>DISCLAIMER: This platform is for educational and research purposes only. No financial advice. No guarantees of profit. Past performance does not guarantee future results.</p>
      </section>

      {/* CTA */}
      <section className="cta">
        <h2>Ready to evolve your trading?</h2>
        <button className="btn-cta" onClick={() => onNavigate('signup')}>
          Start Paper Trading Free
        </button>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <span className="logo-icon">⚡</span>
              <span>QuantAI</span>
            </div>
            <p>Democratizing institutional-grade crypto trading strategies with AI-powered insights and paper trading.</p>
          </div>
          
          <div className="footer-section">
            <h4>Product</h4>
            <ul>
              <li><a href="#features">Features</a></li>
              <li><a href="#pricing">Pricing</a></li>
              <li><a href="#">Roadmap</a></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4>Resources</h4>
            <ul>
              <li><a href="#">Documentation</a></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Community</a></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4>Legal</h4>
            <ul>
              <li><a href="#">Terms</a></li>
              <li><a href="#">Privacy</a></li>
              <li><a href="#">Disclaimer</a></li>
            </ul>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>© 2026 QuantAI Inc. All rights reserved.</p>
          <p>This platform is for educational and research purposes only. No financial advice.</p>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
