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
  const [imagesBase64, setImagesBase64] = useState([]); // for offline queueing
  const [isRecording, setIsRecording] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recordingStartTime, setRecordingStartTime] = useState(null);
  
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

  const handleImageChange = async (e) => {
    const files = Array.from(e.target.files || []);
    setImages(files);
    // Prepare base64 copies for offline storage
    const toBase64 = (file) => new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve({ name: file.name, type: file.type, dataUrl: reader.result });
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
    try {
      const results = await Promise.all(files.map(toBase64));
      setImagesBase64(results);
    } catch (err) {
      console.error('Failed converting images to base64:', err);
    }
  };

  // Start recording audio using MediaRecorder
  const startVoiceRecording = async () => {
    try {
      // Request high-quality microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,  // Higher sample rate for better quality
          channelCount: 1     // Mono is fine for speech
        } 
      });
      
      // Try to use the best available audio format
      let mimeType = 'audio/webm';
      const supportedTypes = [
        'audio/webm;codecs=opus',  // Best for speech
        'audio/mp4',
        'audio/ogg;codecs=opus',
        'audio/webm'
      ];
      
      for (const type of supportedTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          console.log('Using audio format:', type);
          break;
        }
      }
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 128000  // Higher bitrate for better quality
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data chunks - request data every 100ms for smoother recording
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      // When recording stops, transcribe the audio
      mediaRecorder.onstop = async () => {
        const recordingDuration = recordingStartTime ? (Date.now() - recordingStartTime) / 1000 : 0;
        console.log(`Recording duration: ${recordingDuration.toFixed(2)}s`);
        
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log('Audio recording stopped:', {
          chunks: audioChunksRef.current.length,
          blobSize: audioBlob.size,
          blobType: audioBlob.type,
          mimeType: mimeType,
          duration: recordingDuration
        });
        
        if (audioBlob.size === 0) {
          alert('No audio was recorded. Please try again.');
          return;
        }
        
        if (audioBlob.size < 5000) {
          alert('Recording too short. Please speak for at least 3-5 seconds for accurate transcription.');
          return;
        }
        
        if (recordingDuration < 2) {
          alert('Please record for at least 2-3 seconds. Speak clearly and at normal pace.');
          return;
        }
        
        await handleTranscribe(audioBlob);
      };

      // Start recording with timeslice for regular data chunks
      mediaRecorder.start(100);  // Request data every 100ms
      setIsRecording(true);
      setRecordingStartTime(Date.now());
      console.log('Recording started with high quality settings. Speak your issue description.');
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  // Stop recording
  const stopVoiceRecording = async () => {
    if (mediaRecorderRef.current && isRecording) {
      const duration = recordingStartTime ? (Date.now() - recordingStartTime) / 1000 : 0;
      if (duration < 2) {
        alert('Recording too short! Please record for at least 2-3 seconds.');
        // Cancel this recording
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        audioChunksRef.current = [];
        setRecordingStartTime(null);
        return;
      }
      
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

    const attemptOnlineSubmit = async () => {
      const response = await fetch("http://localhost:8000/api/issues", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error('Network error');
      const data = await response.json();
      setSuccess(true);
      alert(`Issue reported successfully! Issue ID: ${data.issue_id}`);
      // Reset form
      setForm({ category: "", description: "", reporter_name: "", reporter_phone: "", gram_panchayat: "", address: "" });
      setImages([]);
      setImagesBase64([]);
      setVoiceText("");
    };

    const queueOffline = () => {
      const payload = {
        form: { ...form },
        voiceText,
        location,
        imagesBase64,
        createdAt: Date.now(),
      };
      const key = 'offlineReports';
      const existing = JSON.parse(localStorage.getItem(key) || '[]');
      localStorage.setItem(key, JSON.stringify([payload, ...existing]));
      alert('You are offline. Report saved and will auto-sync when back online.');
      setSuccess(true);
    };

    try {
      if (!navigator.onLine) {
        queueOffline();
      } else {
        await attemptOnlineSubmit();
      }
    } catch (err) {
      console.warn('Submit failed, queueing offline:', err);
      queueOffline();
    } finally {
      setLoading(false);
    }
  };

  // Auto-sync offline queue when back online
  useEffect(() => {
    const syncQueue = async () => {
      const key = 'offlineReports';
      const queue = JSON.parse(localStorage.getItem(key) || '[]');
      if (!queue.length) return;
      for (const item of [...queue]) {
        try {
          const fd = new FormData();
          fd.append('category', item.form.category);
          fd.append('description', item.form.description);
          fd.append('reporter_name', item.form.reporter_name);
          fd.append('reporter_phone', item.form.reporter_phone);
          fd.append('gram_panchayat', item.form.gram_panchayat);
          fd.append('latitude', item.location.latitude);
          fd.append('longitude', item.location.longitude);
          fd.append('address', item.form.address);
          if (item.voiceText) fd.append('voice_description', item.voiceText);
          // Reconstruct images from base64
          (item.imagesBase64 || []).forEach((img, idx) => {
            try {
              const arr = img.dataUrl.split(',');
              const mime = img.type || 'image/jpeg';
              const bstr = atob(arr[1]);
              let n = bstr.length; const u8arr = new Uint8Array(n);
              while (n--) u8arr[n] = bstr.charCodeAt(n);
              const blob = new Blob([u8arr], { type: mime });
              const file = new File([blob], img.name || `image_${idx}.jpg`, { type: mime });
              fd.append('images', file);
            } catch {}
          });
          const resp = await fetch('http://localhost:8000/api/issues', { method: 'POST', body: fd });
          if (!resp.ok) throw new Error('sync failed');
          // remove from queue
          const rest = JSON.parse(localStorage.getItem(key) || '[]').filter((q) => q.createdAt !== item.createdAt);
          localStorage.setItem(key, JSON.stringify(rest));
        } catch (e) {
          // keep in queue and stop to retry later
          break;
        }
      }
    };
    window.addEventListener('online', syncQueue);
    // Try once on mount
    if (navigator.onLine) syncQueue();
    return () => window.removeEventListener('online', syncQueue);
  }, []);

  return (
    <div className="report-issue-container">
      <div className="page-header">
        <div className="page-header-content">
          <div className="page-header-icon">📢</div>
          <div>
            <h1 className="page-title">Report an Issue</h1>
            <p className="page-subtitle">Help make your community better by reporting local issues. Your voice matters!</p>
          </div>
        </div>
        <div className="features-badges">
          <span className="feature-badge">🎤 Voice Input</span>
          <span className="feature-badge">📍 GPS Location</span>
          <span className="feature-badge">📸 Photo Upload</span>
        </div>
      </div>

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
          {loading ? (
            <>
              <span className="spinner"></span>
              Submitting...
            </>
          ) : (
            <>
              📤 Submit Issue Report
            </>
          )}
        </button>

        {success && (
          <div className="success-message">
            <div className="success-icon">✅</div>
            <div>
              <strong>Issue Reported Successfully!</strong>
              <p>Thank you for helping improve your community. You'll receive updates on the progress.</p>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
