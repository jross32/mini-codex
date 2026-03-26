import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="page-container">
      <div className="page">
        <section className="hero">
        <p className="eyebrow">404</p>
        <h1>Page not found</h1>
        <p className="lede">The page you were looking for doesn&apos;t exist yet. Head back home.</p>
        <Link to="/" className="button primary">
          Go home
        </Link>
      </section>
      </div>
    </div>
  );
}
