'use client';

import React from 'react';

export default function MemoryPanel({ 
  currentSession, 
  memoryContext, 
  ragStats, 
  sessionHistory, 
  backendStatus,
  checkBackendStatus
}) {
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl shadow-xl border border-white/20 p-4 space-y-4 overflow-y-auto">
      <h2 className="text-lg font-semibold text-white mb-3">Memory & History</h2>

      {/* RAG Stats */}
      {ragStats && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-purple-200">Memory Stats</h3>
          <div className="text-xs space-y-1 text-slate-300">
            <div>📚 {ragStats.total_sessions} sessions</div>
            <div>🔍 {ragStats.faiss_index_size} vectors</div>
          </div>
        </div>
      )}

      {/* Backend Status Info */}
      {backendStatus === 'offline' && (
        <div className="mt-4 p-3 bg-red-900/50 rounded-lg border border-red-300/30">
          <p className="text-sm text-red-200 mb-2">
          ⚠️ <strong>AI Backend Offline</strong> The AI processing service is not available. Text chat will work with fallback responses, but file processing requires the backend to be running.
          </p>
          <button
            onClick={checkBackendStatus}
            className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      )}
      

      


      {/* Session History */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-purple-200">Recent Sessions</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {sessionHistory.length > 0 ? (
              sessionHistory.map((session, index) => (
                <div key={index} className="text-xs bg-slate-800/50 p-2 rounded border border-white/10">
                  <div className="font-medium text-purple-200 text-xs">
                    {formatTimestamp(session.timestamp)}
                  </div>
                  <div className="text-slate-300 mt-1 text-xs leading-tight">{session.summary.substring(0, 120)}...</div>
                  {session.metadata && (
                    <div className="text-slate-400 mt-1 text-xs">
                      📷{session.metadata.image_count} 🎵{session.metadata.audio_count} 💬{session.metadata.interaction_count}
                    </div>
                  )}
                  <button
                    onClick={() => {
                      const historyResponse = `Here's what we discussed in this session:\n\n**Session from ${formatTimestamp(session.timestamp)}:**\n\n${session.summary}\n\nWould you like to continue from where we left off?`;
                      const message = {
                        type: 'assistant',
                        content: historyResponse,
                        timestamp: new Date().toISOString()
                      };
                      window.postMessage({ type: 'ADD_CHAT_MESSAGE', message }, '*');
                    }}
                    className="mt-2 px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors w-full"
                  >
                    Continue from here
                  </button>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 text-center py-4">
                No previous sessions yet. Start your first session!
              </div>
            )}
          </div>
        </div>
    </div>
  );
} 