import React, { useState, useEffect, useRef } from "react";

export default function ReportIssue() {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    category: "",
    description: "",
    reporter_name: "",
    reporter_phone: "",
    gram_panchayat: "",
    address: "",
  });
  const [location, setLocation] = useState(null);
  const [images, setImages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  
  // Refs for MediaRecorder
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    fetchCategories();
    getLocation();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/categories");
      const data = await response.json();
      setCategories(data.categories);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          console.error("Error getting location:", error);
          alert("Please enable location services to report issues");
        }
      );
    }
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    setImages(files);
  };

  // Start recording audio using MediaRecorder
  const startVoiceRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data chunks
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      // When recording stops, transcribe the audio
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Audio recording stopped:', {
          chunks: audioChunksRef.current.length,
          blobSize: audioBlob.size,
          blobType: audioBlob.type
        });
        
        if (audioBlob.size === 0) {
          alert('No audio was recorded. Please try again.');
          return;
        }
        
        if (audioBlob.size < 1000) {
          alert('Recording too short. Please speak for at least 1-2 seconds.');
          return;
        }
        
        await handleTranscribe(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('Recording started. Speak your issue description.');
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  // Stop recording
  const stopVoiceRecording = async () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      console.log('Recording stopped. Transcribing now...');
    }
  };

  // Transcribe audio using Groq Whisper
  const handleTranscribe = async (audioBlob) => {
    setTranscribing(true);
    try {
      const formData = new FormData();
      // Determine file extension based on blob type
      const fileExtension = audioBlob.type.includes('webm') ? 'webm' : 
                           audioBlob.type.includes('mp4') ? 'mp4' :
                           audioBlob.type.includes('wav') ? 'wav' : 'webm';
      formData.append("file", audioBlob, `audio.${fileExtension}`);

      console.log('Sending audio for transcription:', {
        size: audioBlob.size,
        type: audioBlob.type,
        filename: `audio.${fileExtension}`
      });

      const response = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      console.log('Transcription response:', result);
      
      if (result.success && result.transcript) {
        // Set transcribed text to description field
        setVoiceText(result.transcript);
        setForm({ ...form, description: result.transcript });
        console.log('Transcription successful:', result.transcript);
      } else {
        const errorMsg = result.error || 'No text could be transcribed from the audio.';
        alert(errorMsg);
        console.error('Transcription error:', result);
      }
    } catch (error) {
      console.error('Transcription failed:', error);
      alert('Transcription failed. Please try again.');
    }
    setTranscribing(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!location) {
      alert("Please enable location services");
      return;
    }

    setLoading(true);
    setSuccess(false);

    const formData = new FormData();
    formData.append("category", form.category);
    formData.append("description", form.description);
    formData.append("reporter_name", form.reporter_name);
    formData.append("reporter_phone", form.reporter_phone);
    formData.append("gram_panchayat", form.gram_panchayat);
    formData.append("latitude", location.latitude);
    formData.append("longitude", location.longitude);
    formData.append("address", form.address);
    
    if (voiceText) {
      formData.append("voice_description", voiceText);
    }

    images.forEach((image) => {
      formData.append("images", image);
    });

    try {
      const response = await fetch("http://localhost:8000/api/issues", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(true);
        alert(`Issue reported successfully! Issue ID: ${data.issue_id}`);
        
        // Reset form
        setForm({
          category: "",
          description: "",
          reporter_name: "",
          reporter_phone: "",
          gram_panchayat: "",
          address: "",
        });
        setImages([]);
        setVoiceText("");
      } else {
        alert("Failed to submit issue. Please try again.");
      }
    } catch (error) {
      console.error("Error submitting issue:", error);
      alert("Error submitting issue. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-issue-container">
      <h2>📢 Report an Issue</h2>
      <p className="subtitle">Help make your village better by reporting local issues</p>

      <form onSubmit={handleSubmit} className="report-form">
        <div className="form-group">
          <label htmlFor="category">Issue Category *</label>
          <div className="category-grid">
            {categories.map((cat) => (
              <button
                key={cat.name}
                type="button"
                className={`category-btn ${form.category === cat.name ? "selected" : ""}`}
                onClick={() => setForm({ ...form, category: cat.name })}
              >
                <span className="category-btn-icon">{cat.icon}</span>
                <span className="category-btn-name">{cat.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <div className="voice-input-group">
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Describe the issue in detail..."
              rows="4"
              required
            />
            {!isRecording ? (
              <button
                type="button"
                className="voice-btn"
                onClick={startVoiceRecording}
                title="Use voice input (Groq Whisper)"
              >
                🎤 Start Recording
              </button>
            ) : (
              <button
                type="button"
                className="voice-btn recording"
                onClick={stopVoiceRecording}
                title="Stop recording"
              >
                🔴 Stop Recording
              </button>
            )}
          </div>
          {transcribing && (
            <p className="transcribing-text">⏳ Transcribing audio with Groq Whisper...</p>
          )}
          {voiceText && (
            <p className="voice-text-preview">✅ Transcribed: "{voiceText}"</p>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="reporter_name">Your Name *</label>
            <input
              type="text"
              id="reporter_name"
              name="reporter_name"
              value={form.reporter_name}
              onChange={handleChange}
              placeholder="Enter your name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reporter_phone">Phone Number *</label>
            <input
              type="tel"
              id="reporter_phone"
              name="reporter_phone"
              value={form.reporter_phone}
              onChange={handleChange}
              placeholder="10-digit mobile number"
              pattern="[0-9]{10}"
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="gram_panchayat">Gram Panchayat *</label>
          <input
            type="text"
            id="gram_panchayat"
            name="gram_panchayat"
            value={form.gram_panchayat}
            onChange={handleChange}
            placeholder="Enter your gram panchayat name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="address">Location/Address *</label>
          <input
            type="text"
            id="address"
            name="address"
            value={form.address}
            onChange={handleChange}
            placeholder="Street, landmark, village"
            required
          />
          {location && (
            <p className="location-info">
              📍 GPS: {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
            </p>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="images">Upload Photos (Optional)</label>
          <input
            type="file"
            id="images"
            accept="image/*"
            multiple
            onChange={handleImageChange}
          />
          {images.length > 0 && (
            <p className="file-count">📸 {images.length} photo(s) selected</p>
          )}
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Submitting..." : "📤 Submit Issue"}
        </button>

        {success && (
          <div className="success-message">
            ✅ Issue reported successfully! You will receive SMS updates.
          </div>
        )}
      </form>
    </div>
  );
}
