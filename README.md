# Neuroflow - Complete Offline AI Tutor with RAG Memory

A sophisticated, completely offline AI tutoring system that combines multimodal analysis with persistent learning memory using local RAG (Retrieval Augmented Generation).

## 🚀 Features

### Core AI Capabilities
- **Gemma 3n 2B Multimodal Analysis**: Native image understanding and audio transcription
- **Ollama Integration**: Enhanced text generation and responses
- **Offline Operation**: No cloud dependencies, runs entirely on local hardware

### Session Management & Memory
- **Persistent Learning**: Session summaries stored in local FAISS vector database
- **Memory Context**: Automatic retrieval of relevant past sessions
- **Chat Interface**: Natural conversation flow with multimodal inputs
- **Session History**: View and manage past learning sessions

### User Interface
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Multiple Input Methods**: File upload, webcam capture, audio recording
- **Voice Output**: Built-in text-to-speech for AI responses (offline)
- **Real-time Processing**: Live feedback and generation indicators
- **Session Controls**: New session, history viewing, memory context

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI    │    │   Flask API     │    │   RAG System    │
│                 │    │                 │    │                 │
│ • File Upload   │◄──►│ • Gemma 2B      │◄──►│ • FAISS Index   │
│ • Chat Interface│    │ • Ollama        │    │ • Session Store │
│ • Session Mgmt  │    │ • Session Track │    │ • Memory Search │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Frontend**: Next.js + React + Tailwind CSS + Web Speech API
- **Backend**: Flask + Python
- **AI Models**: Gemma 3n 2B (multimodal) + Ollama (text enhancement)
- **Voice Synthesis**: Browser-native text-to-speech (offline)
- **Vector Database**: FAISS (local, offline)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama (for Gemma models)

### Setup

1. **Clone and Install Dependencies**
```bash
git clone <repository>
cd StrokeSentry

# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

2. **Install Ollama Models**
```bash
# Install Gemma 3n 2B for multimodal processing
ollama pull gemma3n:2b

# Install Gemma 2B for text enhancement (optional)
ollama pull gemma2:2b
```

3. **Start the System**
```bash
# Terminal 1: Start Flask backend
python app_enhanced.py

# Terminal 2: Start Next.js frontend
npm run dev
```

4. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:5001

## 📖 Usage

### Starting a Session
1. Click "New Session" to begin
2. The system will load relevant memory context from past sessions
3. Upload an image and audio file (or use webcam/recording)
4. Ask questions in the chat interface

### Multimodal Analysis
1. **Image Input**: Upload files or use webcam capture
2. **Audio Input**: Upload files or record directly
3. **Analysis**: Click "Analyze with Gemma" for multimodal processing
4. **Chat**: Ask follow-up questions in the chat interface

### Session Management
- **New Session**: Start fresh with memory context
- **View History**: Browse past sessions and summaries
- **Memory Context**: See relevant past sessions automatically loaded

### Voice Output
- **Auto-speak**: Toggle voice on/off to automatically speak AI responses
- **Manual Control**: Click 🔊 on any AI message to speak it individually
- **Offline Speech**: Uses browser's built-in text-to-speech (no internet required)
- **Voice Settings**: Optimized for clarity with natural speech patterns
- **Stop Control**: Click "Stop" button to halt current speech

## 🧠 RAG Memory System

### How It Works
1. **Session Summarization**: Each session is automatically summarized
2. **Vector Storage**: Summaries are embedded and stored in FAISS
3. **Memory Retrieval**: New sessions query for relevant past sessions
4. **Context Injection**: Relevant memory is injected into new analyses

### Memory Features
- **Offline Storage**: All data stored locally in `rag_data/`
- **Semantic Search**: Find relevant sessions using embeddings
- **Session Metadata**: Track uploads, interactions, and topics
- **Automatic Cleanup**: Temporary files deleted after processing

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Customize RAG data directory
export RAG_DATA_DIR="./custom_rag_data"

# Optional: Customize Flask port
export FLASK_PORT=5001
```

### Model Configuration
- **Gemma 3n 2B**: Optimized for CPU inference
- **FAISS Index**: 384-dimensional embeddings
- **Sentence Transformers**: all-MiniLM-L6-v2 for efficiency

## 🔒 Privacy & Security

### Offline Operation
- **No Cloud Dependencies**: Everything runs locally
- **No Data Transmission**: Files never leave your machine
- **Local Storage**: All session data stored locally
- **No Tracking**: No analytics or telemetry
- **Offline Voice**: Text-to-speech uses browser's built-in system voices

### Data Management
- **Automatic Cleanup**: Temporary files deleted after processing
- **Session Privacy**: Each session isolated and secure
- **Memory Control**: Full control over stored session data

## 🚀 Advanced Features

### Session Workflow
```
New Session → Memory Context → Multimodal Upload → Analysis → Chat → Summary → Store
```

### Memory Integration
- **Contextual Responses**: AI considers past sessions
- **Learning Continuity**: Builds on previous knowledge
- **Topic Tracking**: Automatic topic identification
- **Session Linking**: Connect related sessions

### Future Enhancements
- **Fine-tuned Models**: Custom Gemma models for specific domains
- **Advanced RAG**: More sophisticated memory retrieval
- **Export/Import**: Session data portability
- **Collaborative Features**: Multi-user session sharing

## 🐛 Troubleshooting

### Common Issues
1. **Flask Server Not Starting**: Check port 5001 availability
2. **Model Loading Slow**: First run downloads models (~2GB)
3. **Memory Issues**: Ensure sufficient RAM (8GB+)
4. **Ollama Errors**: Verify Ollama installation and models

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python app_enhanced.py
```

## 📝 License

This project is designed for educational and research purposes. All AI models are used in accordance with their respective licenses.

---

**Neuroflow** - Empowering offline, intelligent tutoring with persistent memory. 🧠✨
