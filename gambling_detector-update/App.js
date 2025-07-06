import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import DomainManagement from './pages/DomainManagement';
import KeywordManagement from './pages/KeywordManagement';
import WhitelistManagement from './pages/WhitelistManagement';
import ScanHistory from './pages/ScanHistory';
import Settings from './pages/Settings';
import TestScan from './pages/TestScan';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#000000', // Apple-style black
    },
    secondary: {
      main: '#757575',
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: "'Noto Sans Thai', 'Helvetica Neue', Arial, sans-serif",
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          padding: '10px 20px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          transition: 'all 0.3s cubic-bezier(.25,.8,.25,1)',
          '&:hover': {
            boxShadow: '0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)',
          },
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          <Navbar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              height: '100vh',
              overflow: 'auto',
              bgcolor: 'background.default',
              p: 3,
              pt: 10,
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/domains" element={<DomainManagement />} />
              <Route path="/keywords" element={<KeywordManagement />} />
              <Route path="/whitelist" element={<WhitelistManagement />} />
              <Route path="/history" element={<ScanHistory />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/test" element={<TestScan />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 