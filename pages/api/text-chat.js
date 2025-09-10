export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { message, session_id, memory_context } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    console.log('💬 Text Chat API: Processing message');
    console.log(`📝 Message: ${message}`);
    console.log(`🆔 Session: ${session_id}`);

    // Create enhanced prompt with memory context
    let enhancedPrompt = `You are Neuroflow, an intelligent AI tutor assistant. Provide helpful, educational responses.

User message: ${message}`;

    if (memory_context) {
      enhancedPrompt = `${memory_context}

${enhancedPrompt}`;
    }

    enhancedPrompt += `

Please provide a helpful, educational response. Keep it concise but informative.`;

    // Send to Flask backend for Ollama processing
    try {
      const flaskResponse = await fetch('http://127.0.0.1:5001/text-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: session_id,
          memory_context: memory_context,
          prompt: enhancedPrompt
        }),
      });

      if (flaskResponse.ok) {
        const flaskData = await flaskResponse.json();
        console.log('✅ Text Chat API: Response generated successfully');
        
        return res.status(200).json({
          response: flaskData.response,
          session_id: flaskData.session_id,
          completion_time: flaskData.completion_time
        });
      } else {
        console.error('❌ Text Chat API: Flask backend error');
        const errorText = await flaskResponse.text();
        
        // Fallback response
        return res.status(200).json({
          response: `I understand you said: "${message}". This is a text-only conversation. You can also upload images and audio for multimodal analysis.`,
          session_id: session_id,
          completion_time: new Date().toISOString()
        });
      }
    } catch (fetchError) {
      console.error('❌ Text Chat API: Connection error to Flask backend:', fetchError);
      
      // Fallback response when backend is unavailable
      return res.status(200).json({
        response: `I understand you said: "${message}". The backend service is currently unavailable, but you can still chat with me. You can also upload images and audio for multimodal analysis when the service is back online.`,
        session_id: session_id,
        completion_time: new Date().toISOString()
      });
    }

  } catch (error) {
    console.error('❌ Text Chat API Error:', error);
    
    // Fallback response
    return res.status(200).json({
      response: "I apologize, but I encountered an error processing your message. Please try again or upload files for multimodal analysis.",
      session_id: req.body.session_id,
      completion_time: new Date().toISOString()
    });
  }
} 