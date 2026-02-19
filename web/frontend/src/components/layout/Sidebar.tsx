import { NavLink } from 'react-router-dom'
import { LayoutDashboard, BarChart3, Play, FlaskConical } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/results', label: 'Results', icon: BarChart3 },
  { to: '/benchmark', label: 'Benchmark', icon: Play },
  { to: '/hypotheses', label: 'Hypotheses', icon: FlaskConical },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>LLM Bench</h1>
        <span>Framework Comparison</span>
      </div>
      <ul className="sidebar-nav">
        {links.map((link) => (
          <li key={link.to}>
            <NavLink to={link.to} className={({ isActive }) => (isActive ? 'active' : '')} end={link.to === '/'}>
              <link.icon size={18} />
              {link.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </aside>
  )
}
