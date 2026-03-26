import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import "./App.css";
import { getMeta, search } from "./api/client";
import { ProfileMenu } from "./components/ProfileMenu";
import { Divisions } from "./routes/Divisions";
import { Matches } from "./routes/Matches";
import { NotFound } from "./routes/NotFound";
import { Players } from "./routes/Players";
import { DataStatusPill } from "./components/DataStatusPill";
import { DivisionDetail } from "./routes/DivisionDetail";
import { Settings } from "./routes/Settings";
import { Teams } from "./routes/Teams";
import { TeamDetail } from "./routes/TeamDetail";
import { PlayerDetail } from "./routes/PlayerDetail";
import { MatchDetail } from "./routes/MatchDetail";
import { CaptainDashboard } from "./routes/CaptainDashboard";
import { Tonight } from "./routes/Tonight";
import { LineupBuilder } from "./routes/LineupBuilder";
import { DivisionStandingsPage } from "./routes/DivisionStandingsPage";
import { TeamRosterHub } from "./routes/TeamRosterHub";
import { NotesDuesAvailability } from "./routes/NotesDuesAvailability";
import { OpponentScouting } from "./routes/OpponentScouting";
import { MatchNightMode } from "./routes/MatchNightMode";
import { CaptainUpdates } from "./routes/CaptainUpdates";
import { AdminPanel } from "./routes/AdminPanel";
import { Login } from "./routes/Login";
import { Signup } from "./routes/Signup";
import { Onboarding } from "./routes/Onboarding";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppGate } from "./components/AppGate";
import { HomeRedirect } from "./components/HomeRedirect";

type NavItem = { path: string; label: string };

const CAPTAIN_NAV: NavItem[] = [
  { path: "/captain/dashboard", label: "Captain Dashboard" },
  { path: "/", label: "Dashboard" },
  { path: "/captain/tonight", label: "Tonight" },
  { path: "/captain/lineup", label: "Lineup Builder" },
  { path: "/division-standings", label: "Division Standings" },
  { path: "/team-roster", label: "Team & Roster" },
  { path: "/captain/updates", label: "Updates" },
  { path: "/players", label: "Players" },
  { path: "/matches", label: "Matches" },
  { path: "/notes", label: "Notes / Dues" },
  { path: "/settings", label: "Settings" },
];

const CLASSIC_NAV: NavItem[] = [
  { path: "/", label: "Dashboard" },
  { path: "/divisions", label: "Divisions" },
  { path: "/teams", label: "Teams" },
  { path: "/players", label: "Players" },
  { path: "/matches", label: "Matches" },
  { path: "/settings", label: "Settings" },
];

function GlobalSearch() {
  const [term, setTerm] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const location = useLocation();

  useEffect(() => {
    const id = setTimeout(() => setDebounced(term.trim()), 200);
    return () => clearTimeout(id);
  }, [term]);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    setOpen(false);
    setTerm("");
    setDebounced("");
  }, [location.pathname]);

  const query = useQuery({
    queryKey: ["global-search", debounced],
    queryFn: () => search(debounced),
    enabled: debounced.length > 1,
  });

  const grouped = useMemo(
    () => ({
      divisions: query.data?.divisions ?? [],
      teams: query.data?.teams ?? [],
      players: query.data?.players ?? [],
      matches: query.data?.matches ?? [],
    }),
    [query.data],
  );

  return (
    <div className="global-search" ref={containerRef}>
      <input
        type="search"
        placeholder="Search..."
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        onFocus={() => setOpen(true)}
      />
      {open && debounced && (
        <div className="search-results">
          <div className="search-header">
            <p className="pill">Results for "{debounced}"</p>
            <button className="ghost-button" onClick={() => setOpen(false)}>
              ✕
            </button>
          </div>

          {grouped.divisions.length ? (
            <div className="search-group">
              <p className="pill">Divisions</p>
              <ul>
                {grouped.divisions.map((div, idx) => (
                  <li key={div.id ?? `div-${idx}`}>
                    <Link to={div.id ? `/divisions/${div.id}` : "/divisions"}>
                      <strong>{div.name ?? "Unnamed division"}</strong>
                      <span className="muted">{div.night ?? "Night TBD"}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {grouped.teams.length ? (
            <div className="search-group">
              <p className="pill">Teams</p>
              <ul>
                {grouped.teams.map((team, idx) => (
                  <li key={team.id ?? `team-${idx}`}>
                    <Link to={team.id ? `/teams/${team.id}` : "/teams"}>
                      <strong>{team.name ?? "Unnamed team"}</strong>
                      <span className="muted">Division {team.division_id ?? "TBD"}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {grouped.players.length ? (
            <div className="search-group">
              <p className="pill">Players</p>
              <ul>
                {grouped.players.map((player, idx) => (
                  <li key={player.id ?? `player-${idx}`}>
                    <Link to={player.id ? `/players/${player.id}` : "/players"}>
                      <strong>{player.name ?? "Unnamed player"}</strong>
                      <span className="muted">Team {player.team_id ?? "TBD"}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {grouped.matches.length ? (
            <div className="search-group">
              <p className="pill">Matches</p>
              <ul>
                {grouped.matches.map((match, idx) => (
                  <li key={match.id ?? `match-${idx}`}>
                    <Link to={match.id ? `/matches/${match.id}` : "/matches"}>
                      <strong>
                        {match.home_team_id ?? "Home"} vs {match.away_team_id ?? "Away"}
                      </strong>
                      <span className="muted">
                        {match.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function Sidebar({ open, onClose, items }: { open: boolean; onClose: () => void; items: NavItem[] }) {
  useEffect(() => {
    onClose();
  }, [useLocation().pathname, onClose]);

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

function BottomNav({ items }: { items: NavItem[] }) {
  const { pathname } = useLocation();
  return (
    <nav className="bottom-nav">
      {items.slice(0, 4).map((item) => (
        <Link key={item.path} to={item.path} className={pathname === item.path ? "active" : ""}>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

function App() {
  const [captainMode, setCaptainMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const closeSidebar = useCallback(() => setSidebarOpen(false), []);
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const location = useLocation();
  const isAuthPage = location.pathname === "/login" || location.pathname === "/signup";

  const navItems = useMemo(() => (captainMode ? CAPTAIN_NAV : CLASSIC_NAV), [captainMode]);

  return (
    <AppGate>
      <div className="app-shell">
        {!isAuthPage && <Sidebar open={sidebarOpen} onClose={closeSidebar} items={navItems} />}
        <div className="main-area">
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
                <ProfileMenu />
              </div>
            </header>
          )}
          <main>
            <Routes>
              <Route path="/captain" element={<ProtectedRoute><CaptainDashboard /></ProtectedRoute>} />
              <Route path="/captain/dashboard" element={<ProtectedRoute><CaptainDashboard /></ProtectedRoute>} />
              <Route path="/tonight" element={<ProtectedRoute><Tonight /></ProtectedRoute>} />
              <Route path="/captain/tonight" element={<ProtectedRoute><Tonight /></ProtectedRoute>} />
              <Route path="/lineup" element={<ProtectedRoute><LineupBuilder /></ProtectedRoute>} />
              <Route path="/captain/lineup" element={<ProtectedRoute><LineupBuilder /></ProtectedRoute>} />
              <Route path="/captain/opponent/:teamId" element={<ProtectedRoute><OpponentScouting /></ProtectedRoute>} />
              <Route path="/captain/updates" element={<ProtectedRoute><CaptainUpdates /></ProtectedRoute>} />
              <Route path="/division-standings" element={<DivisionStandingsPage />} />
              <Route path="/team-roster" element={<TeamRosterHub />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/onboarding" element={<ProtectedRoute allowUnonboarded><Onboarding /></ProtectedRoute>} />
              <Route path="/" element={<ProtectedRoute><HomeRedirect /></ProtectedRoute>} />
              <Route path="/divisions" element={<Divisions />} />
              <Route path="/divisions/:divisionId" element={<DivisionDetail />} />
              <Route path="/teams" element={<Teams />} />
              <Route path="/teams/:teamId" element={<TeamDetail />} />
              <Route path="/players" element={<Players />} />
              <Route path="/players/:playerId" element={<PlayerDetail />} />
              <Route path="/matches" element={<Matches />} />
              <Route path="/matches/:matchId" element={<MatchDetail />} />
              <Route path="/matches/:matchId/mode" element={<ProtectedRoute><MatchNightMode /></ProtectedRoute>} />
              <Route path="/notes" element={<ProtectedRoute><NotesDuesAvailability /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute requireAdmin fallback={<NotFound />}>
                    <AdminPanel />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
        </div>
        {!isAuthPage && <BottomNav items={navItems} />}
      </div>
    </AppGate>
  );
}

export default App;
