'use client';

import React, { useRef, useEffect, useState } from 'react';
import FormattedMessage from './FormattedMessage';

export default function ChatInterface({ 
  chatMessages, 
  userQuery, 
  setUserQuery, 
  handleSendMessage, 
  isGenerating 
}) {
  const chatContainerRef = useRef(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Voice output functions
  const speak = (text) => {
    if (!voiceEnabled || !window.speechSynthesis) return;
    
    // Stop any current speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; // Slightly slower for better clarity
    utterance.pitch = 1.0;
    utterance.volume = 0.8;
    
    // Try to use a female voice if available
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(voice => voice.name.includes('Samantha') || voice.name.includes('Victoria') || voice.name.includes('Alex'));
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // Auto-speak new AI responses
  useEffect(() => {
    if (chatMessages.length > 0) {
      const lastMessage = chatMessages[chatMessages.length - 1];
      if (lastMessage.type === 'assistant' && voiceEnabled) {
        // Extract just the text content (remove markdown formatting)
        const textContent = lastMessage.content.replace(/[#*`]/g, '').replace(/\n+/g, ' ');
        speak(textContent);
      }
    }
  }, [chatMessages, voiceEnabled]);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl shadow-xl border border-white/20 p-6 flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Chat Interface</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              voiceEnabled 
                ? 'bg-green-600 text-white hover:bg-green-700' 
                : 'bg-slate-600 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off'}
          </button>
          {isSpeaking && (
            <button
              onClick={stopSpeaking}
              className="px-3 py-1 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
            >
              ⏹️ Stop
            </button>
          )}
        </div>
      </div>
      
      {/* Chat Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 bg-slate-800/50 rounded-lg border border-white/10"
        style={{ maxHeight: 'calc(100vh - 300px)' }}
      >
        {chatMessages.length === 0 ? (
          <div className="text-center text-slate-300 py-8">
            <p className="text-lg font-medium mb-2">Welcome to Neuroflow! 🧠</p>
            <p className="text-sm mb-4">You can:</p>
            <ul className="text-sm space-y-1 text-left max-w-md mx-auto">
              <li>• 💬 Chat with me using just text</li>
              <li>• 📷 Upload images OR audio for analysis</li>
              <li>• 🎥 Use webcam to capture images</li>
              <li>• 🎤 Record audio directly</li>
            </ul>
            <p className="text-sm mt-4 text-slate-400">Start by typing a message below!</p>
          </div>
        ) : (
          chatMessages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="relative">
                <FormattedMessage content={message.content} type={message.type} />
                <div className="text-xs opacity-70 mt-1 ml-4">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isGenerating && (
          <div className="flex justify-start">
            <div className="bg-slate-700/80 text-slate-200 px-4 py-2 rounded-lg">
              <div className="text-sm font-medium mb-1">Neuroflow</div>
              <div className="text-sm">Generating response...</div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="flex gap-2">
        <textarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message or question... (No files required for text chat!)"
          className="flex-1 px-3 py-2 bg-slate-800/50 border border-white/20 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 text-white placeholder-slate-400"
          rows={2}
        />
        <button
          onClick={handleSendMessage}
          disabled={!userQuery.trim() || isGenerating}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-slate-600 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
} 