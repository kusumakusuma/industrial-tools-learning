import React, { useState, useEffect } from "react";
import "./App.css";

// LESSON 1: React Components - Building blocks of your UI
function App() {
  // LESSON 2: React Hooks - useState for managing data
  const [equipment, setEquipment] = useState([]);
  const [statistics, setStatistics] = useState({
    fleet_availability: 0,
    total_equipment: 0,
    critical_alerts: 0,
    avg_mtbf: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    type: "",
    location: "",
    total_hours: "",
    uptime_hours: "",
    failures: "",
  });

  // LESSON 3: useEffect - Run code when component loads
  useEffect(() => {
    loadEquipmentData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadEquipmentData, 30000);
    return () => clearInterval(interval);
  }, []);

  // LESSON 4: Async data fetching
  const loadEquipmentData = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/equipment");
      const data = await response.json();
      setEquipment(data.equipment);
      setStatistics(data.statistics);
      setLoading(false);
    } catch (error) {
      console.error("Error loading data:", error);
      showMessage(
        "Error connecting to backend. Make sure Flask is running!",
        "error"
      );
      setLoading(false);
    }
  };

  // LESSON 5: Event handlers
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://localhost:5000/api/equipment/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...formData,
          total_hours: parseFloat(formData.total_hours),
          uptime_hours: parseFloat(formData.uptime_hours),
          failures: parseInt(formData.failures),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        showMessage(data.message, "success");
        setFormData({
          name: "",
          type: "",
          location: "",
          total_hours: "",
          uptime_hours: "",
          failures: "",
        });
        setShowAddForm(false);
        loadEquipmentData();
      } else {
        showMessage(data.error, "error");
      }
    } catch (error) {
      showMessage("Error adding equipment", "error");
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete ${name}?`)) return;

    try {
      const response = await fetch(
        `http://localhost:5000/api/equipment/${id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (response.ok) {
        showMessage(data.message, "success");
        loadEquipmentData();
      } else {
        showMessage(data.error, "error");
      }
    } catch (error) {
      showMessage("Error deleting equipment", "error");
    }
  };

  const showMessage = (text, type) => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: "", type: "" }), 5000);
  };

  // LESSON 6: Conditional rendering
  if (loading) {
    return <div className="loading-screen">Loading dashboard...</div>;
  }

  // LESSON 7: JSX - JavaScript XML syntax
  return (
    <div className="App">
      <header className="dashboard-header">
        <h1>⚙️ Reliability Dashboard</h1>
        <p>React-Powered Equipment Monitoring</p>
      </header>

      {/* LESSON 8: Component composition */}
      <main className="dashboard-main">
        {/* Message display */}
        {message.text && (
          <div className={`message ${message.type}`}>{message.text}</div>
        )}

        {/* Metrics Grid */}
        <div className="metrics-grid">
          <MetricCard
            label="Fleet Availability"
            value={`${statistics.fleet_availability}%`}
            status={
              statistics.fleet_availability >= 95
                ? "good"
                : statistics.fleet_availability >= 90
                ? "fair"
                : "poor"
            }
            subtitle="Average across fleet"
          />
          <MetricCard
            label="Total Equipment"
            value={statistics.total_equipment}
            subtitle="Active units"
          />
          <MetricCard
            label="Critical Alerts"
            value={statistics.critical_alerts}
            status={statistics.critical_alerts > 0 ? "poor" : "good"}
            subtitle="Below 90% availability"
          />
          <MetricCard
            label="Average MTBF"
            value={`${statistics.avg_mtbf}h`}
            subtitle="Fleet average"
          />
        </div>

        {/* Add Equipment Button */}
        <div className="actions-bar">
          <button
            className="btn btn-primary"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? "✕ Cancel" : "+ Add Equipment"}
          </button>
        </div>

        {/* Add Equipment Form */}
        {showAddForm && (
          <div className="add-form-container">
            <h2>Add New Equipment</h2>
            <form onSubmit={handleSubmit} className="equipment-form">
              <div className="form-row">
                <input
                  type="text"
                  name="name"
                  placeholder="Equipment Name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
                <input
                  type="text"
                  name="type"
                  placeholder="Type (e.g., Pump)"
                  value={formData.type}
                  onChange={handleInputChange}
                />
                <input
                  type="text"
                  name="location"
                  placeholder="Location"
                  value={formData.location}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-row">
                <input
                  type="number"
                  name="total_hours"
                  placeholder="Total Hours"
                  value={formData.total_hours}
                  onChange={handleInputChange}
                  step="0.1"
                  required
                />
                <input
                  type="number"
                  name="uptime_hours"
                  placeholder="Uptime Hours"
                  value={formData.uptime_hours}
                  onChange={handleInputChange}
                  step="0.1"
                  required
                />
                <input
                  type="number"
                  name="failures"
                  placeholder="Failures"
                  value={formData.failures}
                  onChange={handleInputChange}
                  min="0"
                  required
                />
              </div>
              <button type="submit" className="btn btn-success">
                Add Equipment
              </button>
            </form>
          </div>
        )}

        {/* Equipment Table */}
        <div className="equipment-table">
          <h2>Equipment Status</h2>
          {equipment.length === 0 ? (
            <p className="no-data">
              No equipment found. Add some to get started!
            </p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Equipment</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Availability</th>
                  <th>MTBF</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {equipment.map((eq) => (
                  <EquipmentRow
                    key={eq.id}
                    equipment={eq}
                    onDelete={handleDelete}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}

// LESSON 9: Reusable Components
function MetricCard({ label, value, status, subtitle }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${status ? `status-${status}` : ""}`}>
        {value}
      </div>
      <div className="metric-subtitle">{subtitle}</div>
    </div>
  );
}

// LESSON 10: Component with props
function EquipmentRow({ equipment, onDelete }) {
  const getStatusClass = (status) => {
    switch (status) {
      case "GOOD":
        return "badge-good";
      case "FAIR":
        return "badge-fair";
      case "POOR":
        return "badge-poor";
      default:
        return "badge-nodata";
    }
  };

  const formatMTBF = (mtbf) => {
    if (!mtbf || mtbf >= 999999) return "No failures";
    return `${mtbf.toFixed(1)}h`;
  };

  return (
    <tr>
      <td>
        <strong>{equipment.name}</strong>
      </td>
      <td>{equipment.type || "Unknown"}</td>
      <td>{equipment.location || "Not specified"}</td>
      <td>
        {equipment.availability
          ? `${equipment.availability.toFixed(1)}%`
          : "No data"}
      </td>
      <td>{formatMTBF(equipment.mtbf)}</td>
      <td>
        <span className={`status-badge ${getStatusClass(equipment.status)}`}>
          {equipment.status}
        </span>
      </td>
      <td>
        <button
          className="btn btn-sm"
          onClick={() =>
            alert(
              `Details for ${equipment.name}\nType: ${equipment.type}\nLocation: ${equipment.location}`
            )
          }
        >
          View
        </button>
        <button
          className="btn btn-sm btn-danger"
          onClick={() => onDelete(equipment.id, equipment.name)}
        >
          Delete
        </button>
      </td>
    </tr>
  );
}

export default App;
