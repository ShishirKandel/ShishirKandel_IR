/**
 * Header Component
 *
 * Floating navigation bar with glass morphism effect.
 */

import { Link, useLocation } from 'react-router-dom';
import './Header.css';

export default function Header() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Search', icon: '/' },
    { path: '/classify', label: 'Classify', icon: '/' },
    { path: '/stats', label: 'Stats', icon: '/' },
    { path: '/robustness', label: 'Tests', icon: '/' },
  ];

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <span className="logo-icon">S</span>
          <span className="logo-text">ScholarSearch</span>
        </Link>

        <nav className="nav">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
