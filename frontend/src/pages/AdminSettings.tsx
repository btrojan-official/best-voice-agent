import { useState, useEffect } from "react";
import { apiService } from "../services/api";
import type { Settings } from "../types";
import "./AdminSettings.css";

export default function AdminSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [modelName, setModelName] = useState("");
  const [temperature, setTemperature] = useState(0.7);
  const [newInfoTitle, setNewInfoTitle] = useState("");
  const [newInfoDescription, setNewInfoDescription] = useState("");
  
  // Pricing state
  const [priceInputTokens, setPriceInputTokens] = useState(3.0);
  const [priceOutputTokens, setPriceOutputTokens] = useState(15.0);
  const [priceTranscription, setPriceTranscription] = useState(0.03);
  const [priceTTS, setPriceTTS] = useState(0.30);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await apiService.getSettings();
      setSettings(data);
      setModelName(data.model_name);
      setTemperature(data.temperature);
      setPriceInputTokens(data.price_per_million_input_tokens);
      setPriceOutputTokens(data.price_per_million_output_tokens);
      setPriceTranscription(data.price_per_5s_transcription);
      setPriceTTS(data.price_per_10k_tts_chars);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
      console.error("Error loading settings:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      await apiService.updateSettings({ model_name: modelName });
      setSuccess("Model name updated successfully");
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update model");
    }
  };

  const handleUpdateTemperature = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      await apiService.updateSettings({ temperature });
      setSuccess("Temperature updated successfully");
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update temperature");
    }
  };

  const handleUpdatePricing = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      await apiService.updateSettings({
        price_per_million_input_tokens: priceInputTokens,
        price_per_million_output_tokens: priceOutputTokens,
        price_per_5s_transcription: priceTranscription,
        price_per_10k_tts_chars: priceTTS
      });
      setSuccess("Pricing updated successfully");
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update pricing");
    }
  };

  const handleAddInformation = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!newInfoTitle.trim() || !newInfoDescription.trim()) {
      setError("Title and description are required");
      return;
    }

    try {
      await apiService.addInformation(newInfoTitle, newInfoDescription);
      setSuccess("Information added successfully");
      setNewInfoTitle("");
      setNewInfoDescription("");
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add information");
    }
  };

  const handleRemoveInformation = async (infoId: string) => {
    setError(null);
    setSuccess(null);

    try {
      await apiService.removeInformation(infoId);
      setSuccess("Information removed successfully");
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove information");
    }
  };

  if (loading) {
    return <div className="admin-page">Loading settings...</div>;
  }

  if (!settings) {
    return <div className="admin-page">No settings available</div>;
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="settings-grid">
        <div className="settings-section">
          <h2>Model Configuration</h2>
          
          <form onSubmit={handleUpdateModel} className="settings-form">
            <div className="form-group">
              <label htmlFor="model-name">Model Name</label>
              <input
                type="text"
                id="model-name"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="anthropic/claude-3.5-sonnet"
              />
            </div>
            <button type="submit" className="btn btn-primary">Update Model</button>
          </form>

          <form onSubmit={handleUpdateTemperature} className="settings-form">
            <div className="form-group">
              <label htmlFor="temperature">
                Temperature: {temperature.toFixed(2)}
              </label>
              <input
                type="range"
                id="temperature"
                min="0"
                max="1.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
              />
              <div className="range-labels">
                <span>Conservative (0.0)</span>
                <span>Creative (1.0)</span>
              </div>
            </div>
            <button type="submit" className="btn btn-primary">Update Temperature</button>
          </form>

          <form onSubmit={handleUpdatePricing} className="settings-form">
            <h3>Pricing Configuration</h3>
            <div className="form-group">
              <label htmlFor="price-input-tokens">Price per Million Input Tokens ($)</label>
              <input
                type="number"
                id="price-input-tokens"
                step="0.01"
                min="0"
                value={priceInputTokens}
                onChange={(e) => setPriceInputTokens(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="price-output-tokens">Price per Million Output Tokens ($)</label>
              <input
                type="number"
                id="price-output-tokens"
                step="0.01"
                min="0"
                value={priceOutputTokens}
                onChange={(e) => setPriceOutputTokens(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="price-transcription">Price per 5 Seconds Transcription ($)</label>
              <input
                type="number"
                id="price-transcription"
                step="0.001"
                min="0"
                value={priceTranscription}
                onChange={(e) => setPriceTranscription(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="price-tts">Price per 10k TTS Characters ($)</label>
              <input
                type="number"
                id="price-tts"
                step="0.01"
                min="0"
                value={priceTTS}
                onChange={(e) => setPriceTTS(parseFloat(e.target.value))}
              />
            </div>
            <button type="submit" className="btn btn-primary">Update Pricing</button>
          </form>
        </div>

        <div className="settings-section">
          <h2>Information to Gather</h2>
          
          <div className="info-list">
            {settings.information_to_gather.length === 0 ? (
              <div className="empty-state">No information items configured</div>
            ) : (
              settings.information_to_gather.map((info) => (
                <div key={info.id} className="info-item">
                  <div className="info-content">
                    <h4>{info.title}</h4>
                    <p>{info.description}</p>
                  </div>
                  <button
                    onClick={() => handleRemoveInformation(info.id)}
                    className="btn-remove"
                    title="Remove"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleAddInformation} className="add-info-form">
            <h3>Add New Information</h3>
            <div className="form-group">
              <label htmlFor="info-title">Title</label>
              <input
                type="text"
                id="info-title"
                value={newInfoTitle}
                onChange={(e) => setNewInfoTitle(e.target.value)}
                placeholder="e.g., Customer Email"
              />
            </div>
            <div className="form-group">
              <label htmlFor="info-description">Description</label>
              <textarea
                id="info-description"
                value={newInfoDescription}
                onChange={(e) => setNewInfoDescription(e.target.value)}
                placeholder="e.g., Get the customer's email address for follow-up"
                rows={3}
              />
            </div>
            <button type="submit" className="btn btn-primary">Add Information</button>
          </form>
        </div>
      </div>
    </div>
  );
}
