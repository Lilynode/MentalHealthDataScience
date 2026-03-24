// Vercel Serverless Function: /api
// API index - lists available endpoints

module.exports = async (req, res) => {
  return res.status(200).json({
    service: 'Mental Health Risk Assessment System API',
    version: '1.0.0',
    mode: process.env.MHRAS_API_URL ? 'proxied' : 'demo',
    endpoints: [
      { path: '/api/health', method: 'GET', description: 'Health check endpoint' },
      { path: '/api/screen', method: 'POST', description: 'Screen an individual for mental health risk' },
      { path: '/api/batch-screen', method: 'POST', description: 'Batch screen multiple individuals' }
    ],
    documentation: '/docs'
  });
};
