// Vercel Serverless Function: /api/health
// Health check endpoint

const MHRAS_API_URL = process.env.MHRAS_API_URL;

module.exports = async (req, res) => {
  // Allow GET and HEAD
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      mode: process.env.MHRAS_API_URL ? 'proxied' : 'demo'
    };

    // If backend URL is configured, check the actual API health
    if (MHRAS_API_URL) {
      try {
        const backendResponse = await fetch(`${MHRAS_API_URL}/health`);
        if (backendResponse.ok) {
          health.backend = 'connected';
        } else {
          health.backend = 'error';
          health.status = 'degraded';
        }
      } catch (e) {
        health.backend = 'unreachable';
        health.status = 'degraded';
      }
    }

    return res.status(200).json(health);

  } catch (error) {
    console.error('Health check error:', error);
    return res.status(500).json({
      status: 'error',
      error: error.message
    });
  }
};
