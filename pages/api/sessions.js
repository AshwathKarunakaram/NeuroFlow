export default async function handler(req, res) {
  const { method } = req;

  try {
    switch (method) {
      case 'POST':
        // Start new session
        return await handleNewSession(req, res);
      
      case 'GET':
        // Get session history or current session
        const { type } = req.query;
        if (type === 'history') {
          return await handleGetHistory(req, res);
        } else if (type === 'current') {
          return await handleGetCurrent(req, res);
        } else if (type === 'stats') {
          return await handleGetStats(req, res);
        } else {
          return res.status(400).json({ error: 'Invalid type parameter' });
        }
      
      default:
        return res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('❌ Sessions API Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleNewSession(req, res) {
  try {
    const { userQuery = '' } = req.body;

    console.log('🆕 Sessions API: Starting new session');
    if (userQuery) {
      console.log(`📝 Sessions API: User query: ${userQuery}`);
    }

    try {
      const flaskResponse = await fetch('http://127.0.0.1:5001/new_session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_query: userQuery }),
      });

      if (!flaskResponse.ok) {
        const errorText = await flaskResponse.text();
        console.error(`❌ Sessions API: Flask error: ${flaskResponse.status} - ${errorText}`);
        // Return fallback session data instead of error
        return res.status(200).json({
          status: 'success',
          session_id: `session_${Date.now()}`,
          memory_context: ''
        });
      }

      const flaskData = await flaskResponse.json();
      console.log('✅ Sessions API: New session started successfully');

      return res.status(200).json(flaskData);

    } catch (fetchError) {
      console.error('❌ Sessions API: Connection error to Flask backend:', fetchError);
      // Return fallback session data when backend is unavailable
      return res.status(200).json({
        status: 'success',
        session_id: `session_${Date.now()}`,
        memory_context: ''
      });
    }

  } catch (error) {
    console.error('❌ Sessions API: Error starting new session:', error);
    return res.status(500).json({ error: 'Failed to start new session' });
  }
}

async function handleGetHistory(req, res) {
  try {
    const { limit = 10 } = req.query;

    console.log(`📚 Sessions API: Getting session history (limit: ${limit})`);

    try {
      const flaskResponse = await fetch(`http://127.0.0.1:5001/session_history?limit=${limit}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!flaskResponse.ok) {
        const errorText = await flaskResponse.text();
        console.error(`❌ Sessions API: Flask error: ${flaskResponse.status} - ${errorText}`);
        // Return empty history instead of error
        return res.status(200).json({ status: 'success', history: [] });
      }

      const flaskData = await flaskResponse.json();
      console.log(`✅ Sessions API: Retrieved ${flaskData.history?.length || 0} sessions`);

      return res.status(200).json(flaskData);

    } catch (fetchError) {
      console.error('❌ Sessions API: Connection error to Flask backend:', fetchError);
      // Return empty history when backend is unavailable
      return res.status(200).json({ status: 'success', history: [] });
    }

  } catch (error) {
    console.error('❌ Sessions API: Error getting session history:', error);
    return res.status(500).json({ error: 'Failed to get session history' });
  }
}

async function handleGetCurrent(req, res) {
  try {
    console.log('📋 Sessions API: Getting current session info');

    const flaskResponse = await fetch('http://127.0.0.1:5001/current_session', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!flaskResponse.ok) {
      const errorText = await flaskResponse.text();
      console.error(`❌ Sessions API: Flask error: ${flaskResponse.status} - ${errorText}`);
      return res.status(500).json({ error: 'Failed to get current session' });
    }

    const flaskData = await flaskResponse.json();
    console.log('✅ Sessions API: Retrieved current session info');

    return res.status(200).json(flaskData);

  } catch (error) {
    console.error('❌ Sessions API: Error getting current session:', error);
    return res.status(500).json({ error: 'Failed to get current session' });
  }
}

async function handleGetStats(req, res) {
  try {
    console.log('📊 Sessions API: Getting RAG stats');

    try {
      const flaskResponse = await fetch('http://127.0.0.1:5001/rag_stats', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!flaskResponse.ok) {
        const errorText = await flaskResponse.text();
        console.error(`❌ Sessions API: Flask error: ${flaskResponse.status} - ${errorText}`);
        // Return fallback stats instead of error
        return res.status(200).json({ 
          status: 'success', 
          stats: {
            total_sessions: 0,
            faiss_index_size: 0
          }
        });
      }

      const flaskData = await flaskResponse.json();
      console.log('✅ Sessions API: Retrieved RAG stats');

      return res.status(200).json(flaskData);

    } catch (fetchError) {
      console.error('❌ Sessions API: Connection error to Flask backend:', fetchError);
      // Return fallback stats when backend is unavailable
      return res.status(200).json({ 
        status: 'success', 
        stats: {
          total_sessions: 0,
          faiss_index_size: 0
        }
      });
    }

  } catch (error) {
    console.error('❌ Sessions API: Error getting RAG stats:', error);
    return res.status(500).json({ error: 'Failed to get RAG stats' });
  }
} 