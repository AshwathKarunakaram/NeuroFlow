'use client';

import React from 'react';

export default function FormattedMessage({ content, type }) {
  const speakMessage = () => {
    if (window.speechSynthesis) {
      // Stop any current speech
      window.speechSynthesis.cancel();
      
      // Clean the text (remove markdown formatting)
      const cleanText = content.replace(/[#*`]/g, '').replace(/\n+/g, ' ');
      
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      
      // Try to use a female voice if available
      const voices = window.speechSynthesis.getVoices();
      const femaleVoice = voices.find(voice => voice.name.includes('Samantha') || voice.name.includes('Victoria') || voice.name.includes('Alex'));
      if (femaleVoice) {
        utterance.voice = femaleVoice;
      }
      
      window.speechSynthesis.speak(utterance);
    }
  };
  const formatContent = (text) => {
    if (!text) return '';
    
    // Split by lines to process each line separately
    const lines = text.split('\n');
    
    return lines.map((line, lineIndex) => {
      // Handle headers (###, ##, #)
      if (line.startsWith('### ')) {
        return (
          <h3 key={lineIndex} className="text-lg font-bold text-purple-300 mb-2 mt-4 first:mt-0">
            {line.replace('### ', '')}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={lineIndex} className="text-xl font-bold text-blue-300 mb-3 mt-5 first:mt-0">
            {line.replace('## ', '')}
          </h2>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1 key={lineIndex} className="text-2xl font-bold text-green-300 mb-4 mt-6 first:mt-0">
            {line.replace('# ', '')}
          </h1>
        );
      }
      
      // Handle bullet points
      if (line.startsWith('* ') || line.startsWith('- ')) {
        const content = line.replace(/^[\*\-]\s/, '');
        return (
          <li key={lineIndex} className="text-slate-200 ml-4 mb-3 flex items-start">
            <span className="text-purple-400 mr-3 mt-1 text-lg">•</span>
            <div className="flex-1">
              <span className="font-medium text-purple-200">{content.split(':')[0]}</span>
              {content.includes(':') && (
                <span className="text-slate-300">: {content.split(':').slice(1).join(':')}</span>
              )}
            </div>
          </li>
        );
      }
      
      // Handle numbered lists
      if (/^\d+\.\s/.test(line)) {
        return (
          <li key={lineIndex} className="text-slate-200 ml-4 mb-2 flex items-start">
            <span className="text-blue-400 mr-2 mt-1 font-mono">{(lineIndex + 1)}.</span>
            <span>{line.replace(/^\d+\.\s/, '')}</span>
          </li>
        );
      }
      
      // Handle bold text (**text**)
      if (line.includes('**')) {
        const parts = line.split('**');
        return (
          <p key={lineIndex} className="text-slate-200 mb-2">
            {parts.map((part, partIndex) => 
              partIndex % 2 === 1 ? (
                <strong key={partIndex} className="text-yellow-300 font-semibold bg-yellow-900/20 px-1 rounded">{part}</strong>
              ) : (
                <span key={partIndex}>{part}</span>
              )
            )}
          </p>
        );
      }
      
      // Handle italic text (*text*)
      if (line.includes('*') && !line.startsWith('* ')) {
        const parts = line.split('*');
        return (
          <p key={lineIndex} className="text-slate-200 mb-2">
            {parts.map((part, partIndex) => 
              partIndex % 2 === 1 ? (
                <em key={partIndex} className="text-cyan-300 italic">{part}</em>
              ) : (
                <span key={partIndex}>{part}</span>
              )
            )}
          </p>
        );
      }
      
      // Handle code blocks (```code```)
      if (line.includes('```')) {
        return (
          <div key={lineIndex} className="bg-slate-800/50 border border-slate-600 rounded-lg p-3 my-2">
            <code className="text-green-300 font-mono text-sm">
              {line.replace(/```/g, '')}
            </code>
          </div>
        );
      }
      
      // Handle inline code (`code`)
      if (line.includes('`')) {
        const parts = line.split('`');
        return (
          <p key={lineIndex} className="text-slate-200 mb-2">
            {parts.map((part, partIndex) => 
              partIndex % 2 === 1 ? (
                <code key={partIndex} className="bg-slate-800/70 text-green-300 px-1 rounded font-mono text-sm">{part}</code>
              ) : (
                <span key={partIndex}>{part}</span>
              )
            )}
          </p>
        );
      }
      
      // Handle math expressions (simple detection)
      if (line.includes('=') || line.includes('+') || line.includes('-') || line.includes('×') || line.includes('÷')) {
        return (
          <div key={lineIndex} className="bg-purple-900/30 border border-purple-500/50 rounded-lg p-2 my-2">
            <span className="text-purple-200 font-mono">{line}</span>
          </div>
        );
      }
      
      // Handle empty lines
      if (line.trim() === '') {
        return <div key={lineIndex} className="h-3"></div>;
      }
      
      // Handle sentences that end with exclamation marks or questions
      if (line.endsWith('!') || line.endsWith('?')) {
        return (
          <p key={lineIndex} className="text-slate-200 mb-3 text-lg">
            {line}
          </p>
        );
      }
      
      // Handle sentences that start with "Here's" or "Essentially" (summary statements)
      if (line.startsWith("Here's") || line.startsWith("Essentially")) {
        return (
          <p key={lineIndex} className="text-slate-200 mb-3 italic text-cyan-200">
            {line}
          </p>
        );
      }
      
      // Regular text
      return (
        <p key={lineIndex} className="text-slate-200 mb-2 leading-relaxed">
          {line}
        </p>
      );
    });
  };

  // Special styling for different message types
  const getMessageStyle = () => {
    switch (type) {
      case 'system':
        return 'bg-yellow-900/50 text-yellow-200 border border-yellow-500/50';
      case 'user':
        return 'bg-purple-600 text-white';
      default:
        return 'bg-slate-700/80 text-slate-200';
    }
  };

  return (
    <div className={`max-w-[80%] px-4 py-2 rounded-lg ${getMessageStyle()}`}>
      {type !== 'user' && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-slate-300">
              {type === 'system' ? 'Memory Context' : 'NeuroFlow'}
            </span>
          </div>
          {type === 'assistant' && (
            <button
              onClick={speakMessage}
              className="text-slate-400 hover:text-slate-200 transition-colors p-1 rounded"
              title="Speak this message"
            >
              🔊
            </button>
          )}
        </div>
      )}
      <div className="text-sm">
        {formatContent(content)}
      </div>
    </div>
  );
} 