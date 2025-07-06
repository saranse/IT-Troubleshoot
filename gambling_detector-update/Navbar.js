import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Domain as DomainIcon,
  Key as KeywordIcon,
  Block as WhitelistIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  BugReport as TestIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

const menuItems = [
  { text: 'แดชบอร์ด', icon: <DashboardIcon />, path: '/' },
  { text: 'จัดการโดเมน', icon: <DomainIcon />, path: '/domains' },
  { text: 'จัดการคำค้นหา', icon: <KeywordIcon />, path: '/keywords' },
  { text: 'รายการอนุญาต', icon: <WhitelistIcon />, path: '/whitelist' },
  { text: 'ประวัติการค้นหา', icon: <HistoryIcon />, path: '/history' },
  { text: 'ทดสอบการค้นหา', icon: <TestIcon />, path: '/test' },
  { text: 'ตั้งค่า', icon: <SettingsIcon />, path: '/settings' },
];

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          bgcolor: 'background.paper',
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
        },
      }}
    >
      <Box
        sx={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Gambling Detector
        </Typography>
      </Box>
      <List sx={{ pt: 2 }}>
        {menuItems.map((item) => (
          <ListItem
            key={item.text}
            disablePadding
            sx={{
              mb: 1,
              mx: 1,
              borderRadius: 2,
              bgcolor: location.pathname === item.path ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.08)',
              },
            }}
          >
            <IconButton
              onClick={() => navigate(item.path)}
              sx={{
                py: 1.5,
                px: 2,
                width: '100%',
                justifyContent: 'flex-start',
                color: location.pathname === item.path ? 'primary.main' : 'text.primary',
              }}
            >
              <ListItemIcon
                sx={{
                  color: 'inherit',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </IconButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}

export default Navbar; 