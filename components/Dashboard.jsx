'use client';

import React, { useState, useRef, useEffect } from 'react';
import MediaControls from './MediaControls';
import ChatInterface from './ChatInterface';
import MemoryPanel from './MemoryPanel';

export default function Dashboard() {
  // File upload states
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedAudio, setSelectedAudio] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  
  // Processing states
  const [isProcessing, setIsProcessing] = useState(false);
  const [gemmaOutput, setGemmaOutput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Session management states
  const [currentSession, setCurrentSession] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [memoryContext, setMemoryContext] = useState('');

  const [ragStats, setRagStats] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  
  // Chat states
  const [chatMessages, setChatMessages] = useState([]);
  const [userQuery, setUserQuery] = useState('');

  // Initialize session on component mount
  useEffect(() => {
    checkBackendStatus();
    startNewSession();
    loadSessionHistory();
    loadRagStats();
    
    // Listen for messages from MemoryPanel
    const handleMessage = (event) => {
      if (event.data.type === 'ADD_CHAT_MESSAGE') {
        const message = event.data.message;
        setChatMessages(prev => [...prev, message]);
        
        // If it's a user message (like a search command), process it
        if (message.type === 'user') {
          sendTextMessage(message.content);
        }
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/status', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      if (response.ok) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
      }
    } catch (error) {
      console.log('Backend not available:', error);
      setBackendStatus('offline');
    }
  };



  const startNewSession = async (initialQuery = '') => {
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userQuery: initialQuery })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentSession(data.session_id);
        setMemoryContext(data.memory_context || '');
        setChatMessages([]);
        setGemmaOutput('');
        
        // Clear all file states for new session
        setSelectedImage(null);
        setSelectedAudio(null);
        setCapturedImage(null);
        
        // Add memory context message if available
        if (data.memory_context) {
          setChatMessages([{
            type: 'system',
            content: data.memory_context,
            timestamp: new Date().toISOString()
          }]);
        }
        
        // Reload session history and stats
        await loadSessionHistory();
        await loadRagStats();
        
        console.log('🆕 New session started:', data.session_id);
      }
    } catch (error) {
      console.error('❌ Error starting new session:', error);
    }
  };

  const loadSessionHistory = async () => {
    try {
      const response = await fetch('/api/sessions?type=history&limit=10');
      if (response.ok) {
        const data = await response.json();
        setSessionHistory(data.history || []);
        console.log('📚 Loaded session history:', data.history?.length || 0);
      }
    } catch (error) {
      console.error('❌ Error loading session history:', error);
    }
  };

  const loadRagStats = async () => {
    try {
      const response = await fetch('/api/sessions?type=stats');
      if (response.ok) {
        const data = await response.json();
        setRagStats(data.stats);
        console.log('📊 Loaded RAG stats:', data.stats);
      }
    } catch (error) {
      console.error('❌ Error loading RAG stats:', error);
    }
  };

  const searchPastSessions = async (query) => {
    try {
      const response = await fetch('/api/search-past', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.found_sessions > 0) {
          addChatMessage('assistant', data.summary);
        } else {
          addChatMessage('assistant', 'No relevant past sessions found for your query. Try a different search term or start a new learning session.');
        }
      } else {
        addChatMessage('assistant', 'Sorry, I encountered an error searching past sessions.');
      }
    } catch (error) {
      console.error('❌ Error searching past sessions:', error);
      addChatMessage('assistant', 'Sorry, I encountered an error searching past sessions.');
    }
  };

  const addChatMessage = (type, content, customTimestamp = null) => {
    const message = {
      type,
      content,
      timestamp: customTimestamp || new Date().toISOString()
    };
    setChatMessages(prev => [...prev, message]);
  };

  const processFiles = async (query = '') => {
    // Allow processing with just image OR audio (not requiring both)
    if (!selectedImage && !selectedAudio) {
      alert('Please select at least an image or audio file');
      return;
    }

    setIsProcessing(true);
    setIsGenerating(true);
    setGemmaOutput('');

    // Capture upload timestamp when upload is initiated
    const uploadTime = new Date().toISOString();

    try {
      const formData = new FormData();
      if (selectedImage) {
        formData.append('image', selectedImage);
      }
      if (selectedAudio) {
        formData.append('audio', selectedAudio);
      }
      if (query) {
        formData.append('userQuery', query);
      }

      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setGemmaOutput(data.response);
        
        // Add to chat with proper timestamps
        const uploadDescription = [];
        if (selectedImage) uploadDescription.push('image');
        if (selectedAudio) uploadDescription.push('audio');
        
        // User message timestamp is when upload was initiated
        addChatMessage('user', query || `Uploaded ${uploadDescription.join(' and ')}`, uploadTime);
        
        // Assistant message timestamp is when AI finished processing
        addChatMessage('assistant', data.response, data.completion_time);
        
        // Clear files
        setSelectedImage(null);
        setSelectedAudio(null);
        setCapturedImage(null);
        
      } else {
        const errorData = await response.json();
        setGemmaOutput(`Error: ${errorData.error}`);
      }
    } catch (error) {
      console.error('❌ Error processing files:', error);
      setGemmaOutput('Error processing files. Please try again.');
    } finally {
      setIsProcessing(false);
      setIsGenerating(false);
    }
  };

  const sendTextMessage = async (message) => {
    if (!message.trim()) return;
    
    setIsGenerating(true);
    
    try {
      // Add user message to chat
      addChatMessage('user', message);
      
      // Check if user is asking about previous sessions
      const isAskingAboutHistory = message.toLowerCase().includes('previous') || 
                                  message.toLowerCase().includes('before') || 
                                  message.toLowerCase().includes('last session') ||
                                  message.toLowerCase().includes('what did we talk');
      
      if (isAskingAboutHistory && sessionHistory.length > 0) {
        // Show previous session history
        const latestSession = sessionHistory[0]; // Most recent session
        const historyResponse = `Here's what we discussed in our previous session:\n\n**Session from ${new Date(latestSession.timestamp).toLocaleString()}:**\n\n${latestSession.summary}\n\nWould you like to continue from where we left off?`;
        addChatMessage('assistant', historyResponse);
      } else {
        // Normal text chat
        const response = await fetch('/api/text-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: message,
            session_id: currentSession
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          addChatMessage('assistant', data.response, data.completion_time);
        } else {
          // Fallback response
          addChatMessage('assistant', `I understand you said: "${message}". This is a text-only conversation. You can also upload images and audio for multimodal analysis.`);
        }
      }
      
    } catch (error) {
      console.error('❌ Error sending text message:', error);
      addChatMessage('assistant', 'I apologize, but I encountered an error processing your message. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendMessage = async () => {
    if (!userQuery.trim()) return;
    
    const query = userQuery.trim();
    setUserQuery('');
    
    // If we have files, process them with the query
    if (selectedImage || selectedAudio) {
      await processFiles(query);
    } else {
      // Send as text-only message
      await sendTextMessage(query);
    }
  };



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 px-4 py-2">
      {/* Header */}
      <div className="max-w-full mx-auto mb-6 relative">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          
          {/* Status and Controls */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                backendStatus === 'online' ? 'bg-green-500' : 
                backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
              }`}></div>
              <span className="text-sm text-slate-300">
                {backendStatus === 'online' ? 'AI Backend Online' : 
                 backendStatus === 'offline' ? 'AI Backend Offline' : 'Checking...'}
              </span>
            </div>

            <button
              onClick={() => startNewSession()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              New Session
            </button>
          </div>
        </div>
        
        {/* Absolutely Centered Title */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <h1 
            className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-500 via-blue-500 to-purple-400 bg-clip-text text-transparent"
            style={{
              backgroundSize: '200% 200%',
              animation: 'gradient-shift 3s ease infinite, glow 2s ease-in-out infinite'
            }}
          >
            NeuroFlow
          </h1>
        </div>
      </div>

            <div className="max-w-full mx-auto grid grid-cols-[2fr_6fr_2fr] gap-4 h-[calc(100vh-100px)]">
        {/* Left Panel - Media Controls */}
        <MediaControls
          selectedImage={selectedImage}
          setSelectedImage={setSelectedImage}
          selectedAudio={selectedAudio}
          setSelectedAudio={setSelectedAudio}
          capturedImage={capturedImage}
          setCapturedImage={setCapturedImage}
          isProcessing={isProcessing}
          processFiles={processFiles}
        />

        {/* Center Panel - Chat Interface */}
        <ChatInterface
          chatMessages={chatMessages}
          userQuery={userQuery}
          setUserQuery={setUserQuery}
          handleSendMessage={handleSendMessage}
          isGenerating={isGenerating}
        />

        {/* Right Panel - Memory & History */}
        <MemoryPanel
          currentSession={currentSession}
          memoryContext={memoryContext}
          ragStats={ragStats}
          sessionHistory={sessionHistory}
          backendStatus={backendStatus}
          checkBackendStatus={checkBackendStatus}
        />
      </div>
    </div>
  );
} 