// Vercel Serverless Function: /api/batch-screen
// Batch screening endpoint

const MHRAS_API_URL = process.env.MHRAS_API_URL || 'http://localhost:8000';

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
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Parse body safely - Vercel handles JSON parsing, but handle edge cases
    let requestBody;
    try {
      requestBody = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    } catch (parseError) {
      return res.status(400).json({ error: 'Invalid JSON in request body' });
    }

    if (!requestBody || typeof requestBody !== 'object') {
      return res.status(400).json({ error: 'Request body must be JSON' });
    }

    const { requests } = requestBody;

    if (!requests || !Array.isArray(requests)) {
      return res.status(400).json({ error: 'requests array is required' });
    }

    if (requests.length > 100) {
      return res.status(400).json({ error: 'Maximum 100 requests per batch' });
    }

    // Proxy to backend if configured
    if (process.env.MHRAS_API_URL) {
      const fetchFn = getFetch();
      if (!fetchFn) {
        return res.status(500).json({ error: 'Fetch API unavailable. Ensure Node 18+ runtime or add node-fetch dependency.' });
      }

      const backendResponse = await fetchFn(`${MHRAS_API_URL}/batch-screen`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(req.headers.authorization && { Authorization: req.headers.authorization })
        },
        body: JSON.stringify({ requests })
      });

      if (!backendResponse.ok) {
        const error = await backendResponse.json();
        return res.status(backendResponse.status).json(error);
      }

      const data = await backendResponse.json();
      return res.status(200).json(data);
    }

    // Demo mode: return simulated responses
    const results = [];
    let successful = 0;
    let failed = 0;

    for (const request of requests) {
      try {
        const surveyData = request.survey_data || {};
        const phq9Score = surveyData.phq9_score || 0;
        const gad7Score = surveyData.gad7_score || 0;

        let riskScore = 30;
        if (phq9Score > 15) riskScore += 25;
        else if (phq9Score > 10) riskScore += 15;
        else if (phq9Score > 5) riskScore += 5;

        if (gad7Score > 15) riskScore += 20;
        else if (gad7Score > 10) riskScore += 10;
        else if (gad7Score > 5) riskScore += 5;

        riskScore = Math.min(100, Math.max(0, riskScore));

        let riskLevel = 'LOW';
        if (riskScore > 75) riskLevel = 'CRITICAL';
        else if (riskScore > 60) riskLevel = 'HIGH';
        else if (riskScore > 40) riskLevel = 'MODERATE';

        results.push({
          risk_score: {
            anonymized_id: request.anonymized_id,
            score: riskScore,
            risk_level: riskLevel,
            confidence: 0.75,
            contributing_factors: ['PHQ-9 score', 'GAD-7 score'],
            timestamp: new Date().toISOString()
          },
          recommendations: [],
          explanations: {
            top_features: [],
            counterfactual: '',
            rule_approximation: '',
            clinical_interpretation: ''
          },
          requires_human_review: riskScore > 75,
          alert_triggered: riskScore > 85
        });
        successful++;
      } catch (e) {
        failed++;
        results.push({
          risk_score: {
            anonymized_id: request.anonymized_id || 'unknown',
            score: 0,
            risk_level: 'UNKNOWN',
            confidence: 0,
            contributing_factors: [],
            timestamp: new Date().toISOString()
          },
          recommendations: [],
          explanations: {
            top_features: [],
            counterfactual: `Error: ${e.message}`,
            rule_approximation: '',
            clinical_interpretation: ''
          },
          requires_human_review: true,
          alert_triggered: false
        });
      }
    }

    return res.status(200).json({
      results,
      total: requests.length,
      successful,
      failed
    });

  } catch (error) {
    console.error('Batch screening error:', error);
    return res.status(500).json({ error: 'Internal server error', detail: error.message });
  }
};
