import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

/** Authenticated application layout: sidebar + header + routed main content. */
export function AppShell(): JSX.Element {
  return (
    <div className="app-shell">
      <div className="app-shell__header">
        <Header />
      </div>
      <div className="app-shell__sidebar">
        <Sidebar />
      </div>
      <main className="app-shell__main">
        <div className="app-shell__content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
