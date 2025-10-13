# 🎤 Groq Whisper Voice Transcription Setup Guide

This guide will help you set up the Groq Whisper speech-to-text feature in GramaFix.

---

## 🚀 Quick Start

### 1. Get Groq API Key

1. **Sign up for Groq Cloud**: Go to [https://console.groq.com/](https://console.groq.com/)
2. **Create an account** (free tier available)
3. **Generate API Key**:
   - Go to API Keys section
   - Click "Create API Key"
   - Copy the key (you won't see it again!)

### 2. Configure Backend

1. **Create `.env` file** in the `Backend` folder:
   ```bash
   cd Backend
   ```

2. **Add your Groq API key**:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   MONGODB_URI=mongodb://localhost:27017/GramaFix
   ```

3. **Install the Groq package**:
   ```bash
   pip install groq
   ```
   
   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Update main.py Import

Make sure `main.py` has:
```python
from dotenv import load_dotenv
load_dotenv()  # Load environment variables
```

Add this near the top of `main.py` (after imports):
```python
# Load environment variables
load_dotenv()
```

### 4. Test the Setup

1. **Start the Backend**:
   ```bash
   cd Backend
   uvicorn main:app --reload
   ```

2. **Start the Frontend**:
   ```bash
   cd Frontend
   npm run dev
   ```

3. **Test Voice Input**:
   - Go to http://localhost:5173/report
   - Click "Start Recording" button
   - Allow microphone access
   - Speak clearly: "The road near the village temple has a big pothole"
   - Click "Stop Recording"
   - Wait for transcription (appears in the description field)

---

## 🎯 How It Works

### Frontend Flow:

1. **User clicks "Start Recording"**
   - Browser requests microphone access
   - `MediaRecorder` API starts capturing audio
   - Audio chunks are stored in memory

2. **User clicks "Stop Recording"**
   - Recording stops
   - Audio chunks are combined into a `Blob` (WebM format)
   - Blob is sent to backend API

3. **Backend processes audio**
   - Receives audio file
   - Sends to Groq Whisper API
   - Gets transcription text
   - Normalizes spoken symbols (optional)
   - Returns text to frontend

4. **Frontend displays result**
   - Transcribed text appears in description field
   - User can edit if needed
   - User submits the issue

### Backend Flow:

```
Audio Upload → Save Temp File → Groq Whisper API → Normalize Text → Return Result → Delete Temp File
```

### Symbol Normalization:

The system can convert spoken programming terms to symbols:
- "open parenthesis" → "("
- "close bracket" → "]"
- "colon" → ":"
- "comma" → ","
- etc.

This is useful for technical descriptions or code-related content.

---

## 🔧 Configuration Options

### In `Backend/main.py`:

```python
# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TRANSCRIBE_MODEL = "whisper-large-v3"  # Model to use
ENABLE_SYMBOL_NORMALIZATION = True     # Enable/disable symbol conversion
```

### Available Whisper Models:

- `whisper-large-v3` - Best accuracy, slower (recommended)
- `whisper-large-v3-turbo` - Faster, good accuracy

### Supported Audio Formats:

- WebM (default from browser)
- WAV
- MP3
- M4A
- FLAC

---

## 🌍 Multi-Language Support

Groq Whisper automatically detects the language. It supports:

- **English** (en)
- **Hindi** (hi)
- **Tamil** (ta)
- **Telugu** (te)
- **Marathi** (mr)
- **Bengali** (bn)
- And 90+ other languages!

### To specify a language explicitly:

Update the transcription call in `main.py`:

```python
transcription = client.audio.transcriptions.create(
    file=audio_file,
    model=TRANSCRIBE_MODEL,
    response_format="text",
    language="hi"  # Force Hindi
)
```

---

## 📊 Pricing & Limits

### Groq Free Tier:
- **Requests**: 30 requests/minute
- **Tokens**: 7,000 tokens/minute
- **Daily Limit**: 14,400 requests/day
- **Cost**: **FREE** ✅

### Groq Paid Plans:
- **Pay-as-you-go**: $0.111 per million tokens
- **Higher rate limits**
- **Priority support**

For a rural issue reporting app, the **free tier is more than sufficient**!

---

## 🐛 Troubleshooting

### Issue 1: "Groq API key not configured"

**Solution**: Make sure `.env` file exists with:
```env
GROQ_API_KEY=gsk_your_key_here
```

And `main.py` has:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Issue 2: "Failed to access microphone"

**Solution**:
- Check browser permissions (Settings → Privacy → Microphone)
- Use HTTPS or localhost (HTTP blocks mic on some browsers)
- Try a different browser (Chrome/Edge recommended)

### Issue 3: "ModuleNotFoundError: No module named 'groq'"

**Solution**:
```bash
pip install groq
```

### Issue 4: Transcription is inaccurate

**Solutions**:
- Speak clearly and slowly
- Reduce background noise
- Use a better microphone
- Try `whisper-large-v3` model (most accurate)
- Specify language explicitly if needed

### Issue 5: Audio file too large

**Solution**: Add size limit in frontend:
```javascript
if (audioBlob.size > 25 * 1024 * 1024) { // 25MB limit
    alert('Recording too long. Please keep it under 25MB.');
    return;
}
```

---

## 🎨 Customization

### Change Recording Format:

In `ReportIssue.jsx`:
```javascript
const audioBlob = new Blob(audioChunksRef.current, { 
    type: 'audio/wav'  // Change to wav
});
```

### Add Maximum Recording Time:

```javascript
const startVoiceRecording = async () => {
    // ... existing code
    
    mediaRecorder.start();
    setIsRecording(true);
    
    // Auto-stop after 60 seconds
    setTimeout(() => {
        if (isRecording) {
            stopVoiceRecording();
        }
    }, 60000);
};
```

### Add Visual Recording Indicator:

Add to CSS:
```css
.voice-btn.recording {
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

---

## 📝 Code Reference

### Frontend Code (ReportIssue.jsx):

```javascript
const mediaRecorderRef = useRef(null);
const audioChunksRef = useRef([]);

const startVoiceRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await handleTranscribe(audioBlob);
    };

    mediaRecorder.start();
    setIsRecording(true);
};

const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
    }
};

const handleTranscribe = async (audioBlob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");

    const response = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData,
    });

    const result = await response.json();
    if (result.success) {
        setForm({ ...form, description: result.transcript });
    }
};
```

### Backend Code (main.py):

```python
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_data = await file.read()
    temp_path = f"/tmp/{file.filename}"
    
    with open(temp_path, "wb") as f:
        f.write(audio_data)
    
    client = get_groq_client()
    with open(temp_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="text"
        )
    
    transcript = transcription.strip()
    os.remove(temp_path)
    
    return {"success": True, "transcript": transcript}
```

---

## 🎉 Testing Scenarios

### Test 1: Basic Transcription
**Say**: "The water supply has been cut off for three days in our village."
**Expected**: Accurate transcription in description field

### Test 2: Multi-Language (Hindi)
**Say**: "हमारे गांव में सड़क बहुत खराब है" (Hamāre gānv mein sadak bahut kharāb hai)
**Expected**: Hindi text transcription

### Test 3: Technical Terms
**Say**: "The electricity pole number 247 is damaged"
**Expected**: Numbers and technical terms correctly transcribed

### Test 4: Long Description
**Say**: A detailed 1-minute description of an issue
**Expected**: Complete transcription without cutoff

---

## 🔐 Security Notes

1. **API Key Security**: Never commit `.env` file to Git
2. **Rate Limiting**: Implement rate limits to prevent API abuse
3. **File Size Limits**: Set maximum audio file size
4. **Authentication**: Require login before voice transcription

---

## 📚 Additional Resources

- **Groq Documentation**: https://console.groq.com/docs
- **Whisper Model Details**: https://openai.com/research/whisper
- **MediaRecorder API**: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder

---

## 🆘 Support

If you encounter issues:
1. Check the browser console for errors
2. Check backend logs for API errors
3. Verify Groq API key is valid
4. Test with a simple audio file first

---

**Happy Voice Recording! 🎤✨**
