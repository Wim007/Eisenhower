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

// POST /api/larry
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

// ── CRM proxy ────────────────────────────────────────────────────────────────

function agentsUrl() {
  return process.env.AGENTS_API_URL || 'http://localhost:8000';
}

async function proxyNaarCrm(req, res, methode, pad, body) {
  try {
    const opts = { method: methode, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const response = await fetch(`${agentsUrl()}${pad}`, opts);
    if (response.status === 204) return res.status(204).end();
    const data = await response.json().catch(() => ({}));
    res.status(response.status).json(data);
  } catch (err) {
    console.error('CRM proxy fout:', err.message);
    res.status(500).json({ success: false, message: `CRM niet bereikbaar: ${err.message}` });
  }
}

router.get('/crm/stats',    requireAuth, (req, res) => proxyNaarCrm(req, res, 'GET', '/crm/stats'));
router.get('/crm/pipeline', requireAuth, (req, res) => proxyNaarCrm(req, res, 'GET', '/crm/pipeline'));
router.get('/crm/followups',requireAuth, (req, res) => proxyNaarCrm(req, res, 'GET', '/crm/followups'));

router.get('/crm/leads', requireAuth, (req, res) => {
  const qs = new URLSearchParams();
  if (req.query.status) qs.set('status', req.query.status);
  if (req.query.zoek)   qs.set('zoek',   req.query.zoek);
  if (req.query.sector) qs.set('sector', req.query.sector);
  const pad = `/crm/leads${qs.toString() ? '?' + qs.toString() : ''}`;
  proxyNaarCrm(req, res, 'GET', pad);
});

router.post('/crm/leads',              requireAuth, (req, res) => proxyNaarCrm(req, res, 'POST',   '/crm/leads', req.body));
router.get('/crm/leads/:id',           requireAuth, (req, res) => proxyNaarCrm(req, res, 'GET',    `/crm/leads/${req.params.id}`));
router.put('/crm/leads/:id',           requireAuth, (req, res) => proxyNaarCrm(req, res, 'PUT',    `/crm/leads/${req.params.id}`, req.body));
router.put('/crm/leads/:id/status',    requireAuth, (req, res) => proxyNaarCrm(req, res, 'PUT',    `/crm/leads/${req.params.id}/status`, req.body));
router.delete('/crm/leads/:id',        requireAuth, (req, res) => proxyNaarCrm(req, res, 'DELETE', `/crm/leads/${req.params.id}`));
router.get('/crm/leads/:id/berichten', requireAuth, (req, res) => proxyNaarCrm(req, res, 'GET',    `/crm/leads/${req.params.id}/berichten`));
router.post('/crm/leads/:id/bericht',  requireAuth, (req, res) => proxyNaarCrm(req, res, 'POST',   `/crm/leads/${req.params.id}/bericht`, req.body));

module.exports = router;
