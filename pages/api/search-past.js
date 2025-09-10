export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    // Forward to Flask backend
    const flaskResponse = await fetch('http://127.0.0.1:5001/search_past', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (flaskResponse.ok) {
      const flaskData = await flaskResponse.json();
      return res.status(200).json(flaskData);
    } else {
      const errorData = await flaskResponse.json();
      return res.status(flaskResponse.status).json(errorData);
    }

  } catch (error) {
    console.error('❌ Search past API error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      found_sessions: 0,
      summary: 'Sorry, I encountered an error searching past sessions.'
    });
  }
} 