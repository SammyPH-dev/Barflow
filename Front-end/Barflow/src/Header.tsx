import { useState, useEffect } from "react";
import "./Header.css";

function formatNow(date: Date) {
  const day = date.toLocaleDateString("en-EN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const time = date.toLocaleTimeString("en-EN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${day.charAt(0).toUpperCase() + day.slice(1)} · ${time}`;
}

export default function Header({ page = "Login" }) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000 * 30);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="header">
      <div className="header__left">
        <img className="header__logo" src="/src/assets/logo2.png" alt="logo" />
        <span className="header__brand">BARFLOW</span>
        <span className="header__sep">/</span>
        <span className="header__page">{page}</span>
      </div>

      <div className="header__right">
        <span className="header__date">{formatNow(now)}</span>
        <span className="header__access">
          <img src= "/src/assets/lock.svg" alt="" width={14} height={14} />
          locked
        </span>
      </div>
    </header>
  );
}