# NAV UX IMPLEMENTATION GUIDE
## Desktop Sidebar + Mobile Drawer Navigation

### Changes Required:

#### 1. APP.TSX - Sidebar Component Update
**Replace lines 223-249** with:

```tsx
function Sidebar({ open, onClose, items }: { open: boolean; onClose: () => void; items: NavItem[] }) {
  const { pathname } = useLocation();
  
  useEffect(() => {
    onClose();
  }, [pathname, onClose]);

  return (
    <>
      {open && <div className="sidebar-overlay" onClick={onClose} aria-hidden="true" />}
      
      <aside className={`sidebar ${open ? "open" : ""}`} role="navigation">
        <div className="sidebar-header">
          <span className="brand">apaR</span>
          <button 
            className="icon-button close-button" 
            onClick={onClose} 
            aria-label="Close navigation"
          >
            ✕
          </button>
        </div>
        <nav className="sidebar-nav">
          <ul>
            {items.map((item) => (
              <li key={item.path}>
                <NavLink 
                  to={item.path} 
                  className={({ isActive }) => isActive ? "active" : ""}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar-footer">
          <p className="muted small">apaR · League management</p>
        </div>
      </aside>
    </>
  );
}
```

#### 2. APP.TSX - Header Restructure
**Replace lines 284-300** (the topbar header) with:

```tsx
{!isAuthPage && (
  <header className="topbar">
    <div className="topbar-left">
      <button 
        className="icon-button menu-button" 
        onClick={() => setSidebarOpen(true)} 
        aria-label="Open navigation"
      >
        ☰
      </button>
      <Link to="/" className="brand">
        apaR
      </Link>
    </div>
    
    <div className="topbar-center">
      <div className="pill soft toggle">
        <span>Captain Mode</span>
        <label className="switch">
          <input type="checkbox" checked={captainMode} onChange={() => setCaptainMode((prev) => !prev)} />
          <span className="slider" />
        </label>
      </div>
      <DataStatusPill
        isLoading={metaQuery.isLoading}
        isError={metaQuery.isError}
        data={metaQuery.data}
      />
    </div>
    
    <div className="topbar-right">
      <GlobalSearch />
    </div>
  </header>
)}
```

#### 3. APP.CSS - Complete Sidebar Section Replacement
**Replace lines 58-127** with the complete APP_SHELL section from NAV_CSS_UPDATES.css

#### 4. APP.CSS - Complete Topbar Section Replacement  
**Replace lines 130-160** with the TOPBAR section from NAV_CSS_UPDATES.css

#### 5. APP.CSS - Add Icon Button Styles
**Add after topbar styles** (around line 180) the .icon-button styles from NAV_CSS_UPDATES.css

### Files Created for Reference:
- `NAV_CSS_UPDATES.css` - Complete CSS for navigation
- `APP_UPDATED.tsx.bak` - Reference implementation

### Key Features:
✅ Desktop (≥1024px): Fixed sidebar visible by default
✅ Mobile (<1024px): Slide-in drawer with hamburger toggle  
✅ Active route styling with highlight (blue accent background)
✅ Consistent topbar layout (left/center/right sections)
✅ No layout shifting - fixed widths (280px sidebar)
✅ Smooth animations (280ms transitions)
✅ Overlay backdrop on mobile drawer
✅ Proper z-index layering (sidebar 25, overlay 24, topbar 10)

### Testing Checklist:
- [ ] Desktop: Sidebar fixed on left, content indented
- [ ] Desktop: Menu button hidden, close button hidden
- [ ] Mobile: Sidebar hidden by default
- [ ] Mobile: Hamburger menu visible and clickable
- [ ] Mobile: Drawer slides from left with overlay
- [ ] Mobile: Clicking overlay closes drawer
- [ ] Mobile: Drawer closes on route change
- [ ] Active link highlighted in blue
- [ ] Top bar layout responsive (left/center/right sections)
- [ ] Captain mode toggle visible and functional
- [ ] Search bar visible and functional
- [ ] No layout shift when drawer opens/closes
