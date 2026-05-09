const express = require('express');
const router  = express.Router();

function requireAuth(req, res, next) {
  if (req.session && req.session.adminAuthenticated) return next();
  res.status(401).json({ success: false, message: 'Niet ingelogd.' });
}

// POST /api/login
router.post('/login', (req, res) => {
  const { password } = req.body;
  const adminPassword = process.env.ADMIN_PASSWORD;
  if (!adminPassword) {
    return res.status(500).json({ success: false, message: 'Server configuratiefout.' });
  }
  if (password === adminPassword) {
    req.session.adminAuthenticated = true;
    req.session.save((err) => {
      if (err) {
        console.error('Sessie opslaan mislukt:', err);
        return res.status(500).json({ success: false, message: 'Sessie fout.' });
      }
      return res.json({ success: true });
    });
  } else {
    res.json({ success: false });
  }
});

// GET /api/check
router.get('/check', (req, res) => {
  res.json({ authenticated: !!(req.session && req.session.adminAuthenticated) });
});

// POST /api/logout
router.post('/logout', (req, res) => {
  req.session.destroy(() => res.json({ success: true }));
});

// POST /api/larry — stuurt bericht door naar de echte Eisenhower agents API
router.post('/larry', requireAuth, async (req, res) => {
  const { message, history = [] } = req.body;
  if (!message || !message.trim()) {
    return res.status(400).json({ success: false, message: 'Bericht mag niet leeg zijn.' });
  }

  const agentsUrl = process.env.AGENTS_API_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${agentsUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message.trim(), history }),
    });

    if (!response.ok) {
      const fout = await response.json().catch(() => ({}));
      throw new Error(fout.detail || `Agents API fout: ${response.status}`);
    }

    const data = await response.json();
    res.json({ success: true, reply: data.reply ?? 'Geen antwoord.' });
  } catch (err) {
    console.error('Agents API fout:', err.message);
    res.status(500).json({ success: false, message: `Kan agents niet bereiken: ${err.message}` });
  }
});

// ── CRM proxy routes ─────────────────────────────────────────────────────────

async function crmProxy(req, res, path, method, body) {
  const agentsUrl = process.env.AGENTS_API_URL || 'http://localhost:8000';
  try {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const response = await fetch(`${agentsUrl}${path}`, opts);
    const data = await response.json().catch(() => ({}));
    res.status(response.status).json(data);
  } catch (err) {
    console.error('CRM proxy fout:', err.message);
    res.status(500).json({ success: false, message: `CRM niet bereikbaar: ${err.message}` });
  }
}

router.get('/crm/leads',            requireAuth, (req, res) => crmProxy(req, res, '/crm/leads', 'GET'));
router.post('/crm/leads',           requireAuth, (req, res) => crmProxy(req, res, '/crm/leads', 'POST', req.body));
router.get('/crm/leads/:id',        requireAuth, (req, res) => crmProxy(req, res, `/crm/leads/${req.params.id}`, 'GET'));
router.put('/crm/leads/:id',        requireAuth, (req, res) => crmProxy(req, res, `/crm/leads/${req.params.id}`, 'PUT', req.body));
router.delete('/crm/leads/:id',     requireAuth, (req, res) => crmProxy(req, res, `/crm/leads/${req.params.id}`, 'DELETE'));
router.get('/crm/stats',            requireAuth, (req, res) => crmProxy(req, res, '/crm/stats', 'GET'));
router.post('/crm/leads/:id/sam',   requireAuth, (req, res) => crmProxy(req, res, `/crm/leads/${req.params.id}/sam`, 'POST'));

module.exports = router;
