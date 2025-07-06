import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';

function TestScan() {
  const [domain, setDomain] = useState('');
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    try {
      const response = await axios.get('/api/keywords');
      setKeywords(response.data.filter(k => k.is_active));
    } catch (error) {
      console.error('Error fetching keywords:', error);
      setError('ไม่สามารถโหลดคำค้นหาได้');
    }
  };

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await axios.post('/api/scan/test', {
        domain,
        keywords: keywords.map(k => k.word),
      });
      setResults(response.data);
    } catch (error) {
      console.error('Error scanning domain:', error);
      setError('เกิดข้อผิดพลาดในการค้นหา');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 4 }}>
        ทดสอบการค้นหา
      </Typography>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <TextField
              fullWidth
              label="โดเมน"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="ตัวอย่าง: example.com"
              disabled={loading}
            />
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
              onClick={handleScan}
              disabled={!domain || loading}
              sx={{ height: 56 }}
            >
              ค้นหา
            </Button>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
              คำค้นหาที่ใช้:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {keywords.map((keyword) => (
                <Chip
                  key={keyword.id}
                  label={keyword.word}
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {results && results.length > 0 ? (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            ผลการค้นหา
          </Typography>
          <List>
            {results.map((result, index) => (
              <React.Fragment key={index}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {result.title || result.url}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography
                          component="a"
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          color="primary"
                          sx={{ display: 'block', mb: 1 }}
                        >
                          {result.url}
                        </Typography>
                        {Object.entries(result.matches).map(([keyword, contexts]) => (
                          <Box key={keyword} sx={{ mb: 2 }}>
                            <Typography color="text.secondary" sx={{ mb: 1 }}>
                              พบคำว่า "{keyword}" {contexts.length} ครั้ง:
                            </Typography>
                            {contexts.map((context, i) => (
                              <Typography
                                key={i}
                                variant="body2"
                                sx={{
                                  bgcolor: 'background.default',
                                  p: 1,
                                  borderRadius: 1,
                                  mb: 1,
                                }}
                              >
                                ...{context}...
                              </Typography>
                            ))}
                          </Box>
                        ))}
                      </Box>
                    }
                  />
                </ListItem>
                {index < results.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      ) : results && results.length === 0 ? (
        <Alert severity="info">
          ไม่พบคำค้นหาในโดเมนนี้
        </Alert>
      ) : null}
    </Box>
  );
}

export default TestScan; 