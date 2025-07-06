import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Domain as DomainIcon,
  Key as KeywordIcon,
  Block as WhitelistIcon,
  PlayArrow as PlayIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import axios from 'axios';

function StatCard({ title, value, icon, loading }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {title}
          </Typography>
        </Box>
        {loading ? (
          <CircularProgress size={20} />
        ) : (
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            {value}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    domains: 0,
    keywords: 0,
    whitelist: 0,
    activeScans: 0,
  });
  const [loading, setLoading] = useState(true);
  const [scanGroups, setScanGroups] = useState([]);

  const fetchStats = async () => {
    try {
      const [domainsRes, keywordsRes, whitelistRes] = await Promise.all([
        axios.get('/api/domains'),
        axios.get('/api/keywords'),
        axios.get('/api/whitelist'),
      ]);

      setStats({
        domains: domainsRes.data.length,
        keywords: keywordsRes.data.length,
        whitelist: whitelistRes.data.length,
        activeScans: 0, // TODO: Implement active scans count
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await axios.get('/api/groups');
      setScanGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchGroups();
  }, []);

  const startScan = async (groupId) => {
    try {
      await axios.post(`/api/scan/group/${groupId}`);
      // TODO: Show success notification
    } catch (error) {
      console.error('Error starting scan:', error);
      // TODO: Show error notification
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          แดชบอร์ด
        </Typography>
        <Tooltip title="รีเฟรช">
          <IconButton onClick={fetchStats}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="โดเมนทั้งหมด"
            value={stats.domains}
            icon={<DomainIcon color="primary" />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="คำค้นหา"
            value={stats.keywords}
            icon={<KeywordIcon color="primary" />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="รายการอนุญาต"
            value={stats.whitelist}
            icon={<WhitelistIcon color="primary" />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="กำลังค้นหา"
            value={stats.activeScans}
            icon={<PlayIcon color="primary" />}
            loading={loading}
          />
        </Grid>
      </Grid>

      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        กลุ่มการค้นหา
      </Typography>

      <Grid container spacing={3}>
        {scanGroups.map((group) => (
          <Grid item xs={12} sm={6} md={4} key={group.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  {group.name}
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  {group.domains.length} โดเมน
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={() => startScan(group.id)}
                  >
                    เริ่มค้นหา
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<ScheduleIcon />}
                    onClick={() => {/* TODO: Implement schedule scan */}}
                  >
                    ตั้งเวลา
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default Dashboard;