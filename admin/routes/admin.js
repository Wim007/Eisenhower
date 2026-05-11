const express = require('express');
const router  = express.Router();
const OpenAI  = require('openai');

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

// Systeem prompts per manager
const PROMPT_LARRY = `Je bent Larry, project manager voor SamenOntzorgen — een coöperatief flex-platform voor de Nederlandse zorgsector.

Jouw team:
- Sam: LinkedIn B2B outreach naar zorginstellingen
- Vera: LinkedIn content en thought leadership
- Rosa: Facebook content voor ZZP'ers en deeltijdwerkers
- Finn: LinkedIn warm netwerk outreach (altijd goedkeuring Wim vereist)
- Daan: Facebook DM outreach (altijd goedkeuring Wim vereist)
- Bram: Huisartsen outreach (altijd goedkeuring Wim vereist)
- Iris: Prospect research voor huisartsenpraktijken
- Bax: Senior onderzoeker
- Nova: Deal coaching en pilotgesprekken
- Lena: Intake voor nieuwe zorgprofessionals

Context SamenOntzorgen:
- Coöperatief model: professionals zijn mede-eigenaar, geen commerciële tussenlaag
- Tot 35% goedkoper dan uitzendbureaus
- Juridisch compliant: geen schijnzelfstandigheid / Wet DBA risico
- Warme lead: Laurens (grote zorginstelling)
- Merkstijl: Innocent archetype — rustig, eerlijk, menselijk, nooit salesachtig

Schrijf LinkedIn posts, outreach berichten en strategieën direct uit als Wim daarom vraagt.
Taal: altijd Nederlands. Antwoorden: kort en concreet.`;

const PROMPT_MARINA = `Je bent Marina, project manager voor Matti — een AI-assistent voor mentale ondersteuning van middelbare scholieren (12-21 jaar).

Team: Sophie (school outreach), Josh (Instagram), Maya (community), Zoe (TikTok), Alex (safety), Riley (kwaliteit).
Status: live app, op zoek naar scholen voor pilot van 30-40 leerlingen.
Toon: warm, normaliserend — geen therapietaal. Taal: altijd Nederlands.`;

const PROMPT_SOPHIA = `Je bent Sophia, project manager voor AI Doc — een AI-administratieassistent voor huisartsenpraktijken.

Team: Henri (GP outreach), Esther (strategie), François (content), Marie (compliance).
Status: pilotfase 2026, op zoek naar huisartsenpraktijken.
Toon: medisch-professioneel, praktisch, gericht op tijdsbesparing. Taal: altijd Nederlands.`;

function kiesPrompt(bericht) {
  const b = bericht.toUpperCase();
  if (b.startsWith('[MATTI]')) return PROMPT_MARINA;
  if (b.startsWith('[AI DOC]')) return PROMPT_SOPHIA;
  return PROMPT_LARRY;
}

// POST /api/larry — OpenAI direct vanuit admin panel
router.post('/larry', requireAuth, async (req, res) => {
  const { message, history = [] } = req.body;
  if (!message || !message.trim()) {
    return res.status(400).json({ success: false, message: 'Bericht mag niet leeg zijn.' });
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ success: false, message: 'OPENAI_API_KEY ontbreekt. Voeg deze toe in Railway onder Variables.' });
  }

  const client = new OpenAI({ apiKey });
  const messages = [{ role: 'system', content: kiesPrompt(message.trim()) }];
  for (const m of history.slice(-8)) {
    if (m.role === 'user' || m.role === 'assistant') {
      messages.push({ role: m.role, content: m.content });
    }
  }
  messages.push({ role: 'user', content: message.trim() });

  try {
    const response = await client.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      messages,
      max_tokens: 800,
      temperature: 0.7,
    });
    res.json({ success: true, reply: response.choices[0].message.content });
  } catch (err) {
    console.error('OpenAI fout:', err.message);
    res.status(500).json({ success: false, message: `OpenAI fout: ${err.message}` });
  }
});

// POST /api/kalender/genereer — genereer een maand LinkedIn posts
router.post('/kalender/genereer', requireAuth, async (req, res) => {
  const { project = 'SO', frequentie = 3, startDatum } = req.body;

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return res.status(500).json({ success: false, message: 'OPENAI_API_KEY ontbreekt.' });

  const projectNamen = { SO: 'SamenOntzorgen', MA: 'Matti', AD: 'AI Doc' };
  const projectContext = {
    SO: `SamenOntzorgen is een coöperatief flex-platform voor de zorgsector. Tot 35% goedkoper dan uitzendbureaus. Juridisch compliant (geen Wet DBA risico). Doelgroep: HR-directeuren en bestuurders bij zorginstellingen. Archetype: Innocent — rustig, eerlijk, nooit salesachtig. Gebruik de 5fortyfive schrijfvolgorde: erken het probleem → gevolg van niets doen → gewenste situatie → kleine stap. Nooit harde CTA's als "plan een afspraak".`,
    MA: `Matti is een AI-assistent voor preventieve mentale ondersteuning van middelbare scholieren. Doelgroep LinkedIn: schooldirecteuren, zorgcoördinatoren, beleidsmakers in het onderwijs. Toon: warm, normaliserend, geen therapietaal.`,
    AD: `AI Doc is een AI-administratieassistent voor huisartsenpraktijken (transcriptie, SOAP-verslaglegging). Doelgroep: huisartsen, praktijkmanagers. Toon: professioneel, praktisch, gericht op tijdsbesparing.`
  };

  // Bereken data voor de komende maand
  const start = startDatum ? new Date(startDatum) : new Date();
  const dagen = ['zondag','maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag'];
  const postData = [];
  const postDagen = frequentie === 2 ? [1, 4] : [1, 3, 5]; // ma+do of ma+wo+vr

  for (let week = 0; week < 4; week++) {
    for (const dag of postDagen) {
      const d = new Date(start);
      d.setDate(start.getDate() + week * 7 + ((dag - start.getDay() + 7) % 7));
      if (d >= start) {
        postData.push(d.toISOString().slice(0, 10));
      }
    }
  }
  const aantalPosts = postData.slice(0, 12); // max 12 posts

  const prompt = `Schrijf ${aantalPosts.length} LinkedIn posts voor ${projectNamen[project]}.

Context: ${projectContext[project]}

Regels:
- Elke post is uniek, geen herhaling van hetzelfde thema
- Begin NOOIT met "Ik" of een productpitch
- Begin met een observatie, vraag, cijfer of herkenbare situatie
- Max 200 woorden per post
- Sluit af met een zachte vraag of uitnodiging, nooit met "neem contact op"
- Schrijf in het Nederlands, persoonlijke toon van Wim

Geef de posts terug als JSON array in dit formaat (niets anders, alleen JSON):
[
  {"datum": "${aantalPosts[0]}", "content": "volledige post tekst hier"},
  {"datum": "${aantalPosts[1] || aantalPosts[0]}", "content": "..."},
  ...
]

Datums in volgorde: ${aantalPosts.join(', ')}`;

  try {
    const client = new OpenAI({ apiKey });
    const response = await client.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'Je bent een LinkedIn content expert. Geef altijd alleen geldige JSON terug, geen extra tekst.' },
        { role: 'user', content: prompt }
      ],
      max_tokens: 4000,
      temperature: 0.8,
    });

    const raw = response.choices[0].message.content.trim();
    const jsonStart = raw.indexOf('[');
    const jsonEnd = raw.lastIndexOf(']') + 1;
    const posts = JSON.parse(raw.slice(jsonStart, jsonEnd));
    res.json({ success: true, posts, project });
  } catch (err) {
    console.error('Kalender genereer fout:', err.message);
    res.status(500).json({ success: false, message: `Fout bij genereren: ${err.message}` });
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
