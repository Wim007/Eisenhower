require('dotenv').config();
const express = require('express');
const session = require('express-session');
const path    = require('path');

const adminRoutes = require('./routes/admin');

const app  = express();
const PORT = process.env.PORT || 4000;

// Vertrouw de Railway proxy zodat secure cookies werken via HTTPS
app.set('trust proxy', 1);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: process.env.SESSION_SECRET || 'dev-secret-change-me',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 8 * 60 * 60 * 1000 // 8 uur
  }
}));

app.use(express.static(path.join(__dirname, 'public')));

// API routes
app.use('/api', adminRoutes);

// Login pagina
app.get('/', (req, res) => {
  if (req.session && req.session.adminAuthenticated) {
    return res.redirect('/dashboard');
  }
  res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// Dashboard (server-side beschermd)
app.get('/dashboard', (req, res) => {
  if (!(req.session && req.session.adminAuthenticated)) {
    return res.redirect('/');
  }
  res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

// 404 terug naar login
app.use((req, res) => res.redirect('/'));

app.listen(PORT, () => {
  console.log(`Eisenhower Command Center draait op http://localhost:${PORT}`);
});
