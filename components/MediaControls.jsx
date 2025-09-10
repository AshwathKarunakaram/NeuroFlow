'use client';

import React, { useRef, useState, useEffect } from 'react';

export default function MediaControls({ 
  selectedImage, 
  setSelectedImage, 
  selectedAudio, 
  setSelectedAudio,
  capturedImage,
  setCapturedImage,
  isProcessing,
  processFiles
}) {
  // Webcam states
  const [showWebcam, setShowWebcam] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  // Audio recording states
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [recordingReady, setRecordingReady] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  
  // Refs
  const fileInputRef = useRef(null);
  const audioInputRef = useRef(null);

  // Cleanup audio URL when component unmounts
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startCamera = async () => {
    try {
      console.log('🎥 Starting camera...');
      
      // Stop any existing stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      console.log('✅ Stream obtained:', stream);
      streamRef.current = stream;
      
      // Wait a moment for the video element to be ready
      setTimeout(() => {
        if (videoRef.current) {
          console.log('📹 Setting video srcObject...');
          videoRef.current.srcObject = stream;
          console.log('📹 Video srcObject set:', videoRef.current.srcObject);
          
          // Force the video to load
          videoRef.current.load();
          
          videoRef.current.onloadedmetadata = () => {
            console.log('📹 Video metadata loaded');
            videoRef.current.play().then(() => {
              console.log('▶️ Video started playing');
              setCameraReady(true);
            }).catch(err => {
              console.error('❌ Video play error:', err);
            });
          };
        } else {
          console.error('❌ Video element not found');
        }
      }, 100);
      
      setShowWebcam(true);
    } catch (err) {
      console.error('❌ Camera error:', err);
      alert("Camera access denied or not available.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowWebcam(false);
    setCameraReady(false);
  };

  const captureImage = () => {
    console.log('📸 Attempting to capture image...');
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    console.log('Video element:', !!video);
    console.log('Canvas element:', !!canvas);
    
    if (!video || !canvas) {
      console.error('❌ Video or canvas not found');
      return;
    }

    console.log('Video dimensions:', video.videoWidth, 'x', video.videoHeight);
    console.log('Video ready state:', video.readyState);
    console.log('Video paused:', video.paused);

    const context = canvas.getContext('2d');
    if (!context) {
      console.error('❌ Could not get canvas context');
      return;
    }

    // Check if video has valid dimensions
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.error('❌ Video has no dimensions');
      alert('Camera not ready. Please wait a moment and try again.');
      return;
    }

    try {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      console.log('Canvas size set to:', canvas.width, 'x', canvas.height);
      
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      console.log('✅ Image drawn to canvas');

      canvas.toBlob((blob) => {
        if (blob) {
          console.log('✅ Blob created, size:', blob.size);
          const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
          setCapturedImage(file);
          setSelectedImage(file);
          stopCamera();
        } else {
          console.error('❌ Failed to create blob');
          alert('Failed to capture image. Please try again.');
        }
      }, 'image/jpeg', 0.9);
    } catch (error) {
      console.error('❌ Error capturing image:', error);
      alert('Error capturing image. Please try again.');
    }
  };

  const startRecording = async () => {
    try {
      console.log('🎤 Starting audio recording...');
      setRecordingReady(false);
      setAudioChunks([]);
      
      // Check if getUserMedia and MediaRecorder are supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Microphone access is not supported in this browser.');
        return;
      }
      
      if (!window.MediaRecorder) {
        alert('Audio recording is not supported in this browser.');
        return;
      }
      
      // Stop any existing recording
      if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true
      });
      
      console.log('✅ Audio stream obtained');
      
      // Create MediaRecorder with WAV format if possible
      let recorder;
      const chunks = [];
      
      // Try to use WAV format for better compatibility
      if (MediaRecorder.isTypeSupported('audio/wav')) {
        recorder = new MediaRecorder(stream, { mimeType: 'audio/wav' });
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        recorder = new MediaRecorder(stream, { mimeType: 'audio/mp4' });
      } else {
        recorder = new MediaRecorder(stream);
      }
      
      console.log('🎤 Using format:', recorder.mimeType);
      
      recorder.ondataavailable = (event) => {
        console.log('🎵 Audio chunk received:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstart = () => {
        console.log('🎤 Recording started');
        setRecordingReady(true);
      };
      
      recorder.onstop = () => {
        console.log('🛑 Recording stopped, processing chunks...');
        
        if (chunks.length > 0) {
          const audioBlob = new Blob(chunks, { type: recorder.mimeType });
          console.log('🎵 Audio blob created:', audioBlob.size, 'bytes');
          
          if (audioBlob.size > 0) {
            // Determine file extension based on mime type
            let extension = 'wav';
            if (recorder.mimeType.includes('mp4')) extension = 'mp4';
            else if (recorder.mimeType.includes('webm')) extension = 'webm';
            else if (recorder.mimeType.includes('ogg')) extension = 'ogg';
            
            const fileName = `recording.${extension}`;
            const file = new File([audioBlob], fileName, { type: recorder.mimeType });
            setSelectedAudio(file);
            
            // Create URL for audio playback
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
            console.log('✅ Audio file created:', file.name, file.size, 'bytes');
          } else {
            console.error('❌ Audio blob is empty');
            alert('Recording was too short. Please try recording for at least 1 second.');
          }
        } else {
          console.error('❌ No audio chunks recorded');
          alert('No audio was recorded. Please try again.');
        }
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        setAudioChunks([]);
        setRecordingReady(false);
      };
      
      recorder.onerror = (event) => {
        console.error('❌ Recording error:', event.error);
        alert('Recording error occurred. Please try again.');
        setRecordingReady(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording with 1-second intervals
      recorder.start(1000);
      setMediaRecorder(recorder);
      setIsRecording(true);
      
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      alert(`Microphone access denied: ${error.message}. Please allow microphone permissions and try again.`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      console.log('🛑 Stopping recording...');
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setCapturedImage(null);
    }
  };

  const handleAudioUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedAudio(file);
      // Create URL for audio playback
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl shadow-xl border border-white/20 p-6 space-y-4 overflow-y-auto">
      <h2 className="text-xl font-semibold text-white mb-4">Upload & Controls</h2>
      
      {/* Image Upload */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-purple-200">Image Input</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="block w-full text-sm text-purple-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
        />
        
        {/* Webcam */}
        <div className="space-y-2">
          <button
            onClick={showWebcam ? stopCamera : startCamera}
            className="w-full px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            {showWebcam ? 'Stop Camera' : 'Use Webcam'}
          </button>
          
          {showWebcam && (
            <div className="space-y-2">
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted
                className="w-full h-32 object-cover rounded-lg mb-2 bg-black"
                onError={(e) => console.error('Video error:', e)}
                onLoadStart={() => console.log('Video load start')}
                onLoadedData={() => console.log('Video data loaded')}
              />
              <button
                onClick={captureImage}
                className="w-full px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
              >
                Capture
              </button>
            </div>
          )}
          
          {(selectedImage || capturedImage) && (
            <img
              src={URL.createObjectURL(selectedImage || capturedImage)}
              alt="Selected"
              className="w-full h-28 object-cover rounded-lg mb-1"
              style={{ minHeight: '112px', maxHeight: '112px' }}
            />
          )}
        </div>
      </div>

      {/* Audio Upload */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-purple-200">Audio Input</label>
        <input
          ref={audioInputRef}
          type="file"
          accept="audio/*"
          onChange={handleAudioUpload}
          className="block w-full text-sm text-purple-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
        />
        
        {/* Audio Recording */}
        <div className="space-y-2">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`w-full px-3 py-2 rounded-lg transition-colors text-sm ${
              isRecording 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {isRecording ? 'Stop Recording' : 'Record Audio'}
          </button>
          
          {isRecording && (
            <div className="text-xs text-red-200 text-center">
              Recording... Speak now!
            </div>
          )}
          
          {selectedAudio && (
            <div className="space-y-2">
              <div className="text-sm text-purple-200">
                Audio file selected: {selectedAudio.name}
              </div>
              {audioUrl && (
                <audio 
                  controls 
                  className="w-full"
                  src={audioUrl}
                >
                  Your browser does not support the audio element.
                </audio>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Process Button */}
      <button
        onClick={() => processFiles()}
        disabled={(!selectedImage && !selectedAudio) || isProcessing}
        className={`w-full px-4 py-3 rounded-lg font-medium transition-colors ${
          (!selectedImage && !selectedAudio) || isProcessing
            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
            : 'bg-purple-600 text-white hover:bg-purple-700'
        }`}
      >
        {isProcessing ? 'Processing...' : 'Analyze with Gemma'}
      </button>

      {/* Hidden canvas for webcam capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
} 