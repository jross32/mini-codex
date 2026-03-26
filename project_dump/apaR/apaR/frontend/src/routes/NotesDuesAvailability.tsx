import { useState } from "react";
import { Skeleton } from "../components/Skeleton";

export function NotesDuesAvailability() {
  const [notes, setNotes] = useState("");
  const [dues, setDues] = useState("");
  const [availability, setAvailability] = useState("");

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Notes / Dues / Availability</p>
          <h1>Captain notebook</h1>
          <p className="lede">Track reminders, money, and who can play.</p>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Notes</p>
            <h3>Scouting & reminders</h3>
          </div>
        </div>
        <textarea
          className="textarea"
          rows={4}
          placeholder="Add coaching tips, opponent tendencies..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Dues</p>
            <h3>Track payments</h3>
          </div>
        </div>
        <textarea
          className="textarea"
          rows={3}
          placeholder="Who has paid, who owes, notes on receipts..."
          value={dues}
          onChange={(e) => setDues(e.target.value)}
        />
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Availability</p>
            <h3>In / Out</h3>
          </div>
        </div>
        <textarea
          className="textarea"
          rows={3}
          placeholder="Availability for this week"
          value={availability}
          onChange={(e) => setAvailability(e.target.value)}
        />
      </section>

      {/* Static skeleton for consistency with the rule about loading states */}
      <Skeleton lines={2} />
      </div>
    </div>
  );
}
