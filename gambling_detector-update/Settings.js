import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import axios from 'axios';

function Settings() {
  const [settings, setSettings] = useState({
    telegram_bot_token: '',
    telegram_chat_id: '',
    email_notifications: false,
    email_recipients: '',
    auto_cleanup_days: 7,
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/config/all');
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      setSnackbar({
        open: true,
        message: 'ไม่สามารถโหลดการตั้งค่าได้',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await axios.post('/api/config', settings);
      setSnackbar({
        open: true,
        message: 'บันทึกการตั้งค่าเรียบร้อย',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error saving settings:', error);
      setSnackbar({
        open: true,
        message: 'ไม่สามารถบันทึกการตั้งค่าได้',
        severity: 'error',
      });
    }
  };

  const handleChange = (key) => (event) => {
    setSettings({
      ...settings,
      [key]: event.target.type === 'checkbox' ? event.target.checked : event.target.value,
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 4 }}>
        ตั้งค่า
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            การแจ้งเตือน Telegram
          </Typography>
          <TextField
            fullWidth
            label="Telegram Bot Token"
            value={settings.telegram_bot_token}
            onChange={handleChange('telegram_bot_token')}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Telegram Chat ID"
            value={settings.telegram_chat_id}
            onChange={handleChange('telegram_chat_id')}
            margin="normal"
          />
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            การแจ้งเตือนทางอีเมล
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={settings.email_notifications}
                onChange={handleChange('email_notifications')}
              />
            }
            label="เปิดใช้งานการแจ้งเตือนทางอีเมล"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="อีเมลผู้รับ (คั่นด้วยเครื่องหมาย , )"
            value={settings.email_recipients}
            onChange={handleChange('email_recipients')}
            disabled={!settings.email_notifications}
            helperText="ใส่อีเมลหลายคนโดยคั่นด้วยเครื่องหมายจุลภาค (,)"
            margin="normal"
          />
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            การจัดการข้อมูล
          </Typography>
          <TextField
            type="number"
            label="จำนวนวันที่เก็บประวัติ"
            value={settings.auto_cleanup_days}
            onChange={handleChange('auto_cleanup_days')}
            InputProps={{ inputProps: { min: 1, max: 30 } }}
            helperText="ระบบจะลบประวัติที่เก่ากว่าจำนวนวันที่กำหนดโดยอัตโนมัติ"
            margin="normal"
          />
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={loading}
        >
          บันทึกการตั้งค่า
        </Button>
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Settings; 