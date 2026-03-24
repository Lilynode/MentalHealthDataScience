// Vercel Serverless Function: /api/health
// Health check endpoint

const MHRAS_API_URL = process.env.MHRAS_API_URL;

const getFetch = () => {
  if (typeof fetch !== 'undefined') return fetch;
  if (typeof global !== 'undefined' && typeof global.fetch !== 'undefined') return global.fetch;
  try {
    return require('node-fetch');
  } catch (_e) {
    return null;
  }
};

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
      const fetchFn = getFetch();
      if (!fetchFn) {
        health.backend = 'fetch_unavailable';
        health.status = 'degraded';
      } else {
        try {
          const backendResponse = await fetchFn(`${MHRAS_API_URL}/health`);
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
