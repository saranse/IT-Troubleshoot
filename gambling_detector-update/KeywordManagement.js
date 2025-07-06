import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add as AddIcon } from '@mui/icons-material';
import axios from 'axios';

function KeywordManagement() {
  const [keywords, setKeywords] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [editingKeyword, setEditingKeyword] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/keywords');
      setKeywords(response.data);
    } catch (error) {
      console.error('Error fetching keywords:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (keyword = null) => {
    setEditingKeyword(keyword);
    setNewKeyword(keyword ? keyword.word : '');
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewKeyword('');
    setEditingKeyword(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingKeyword) {
        await axios.put(`/api/keywords/${editingKeyword.id}`, { word: newKeyword });
      } else {
        await axios.post('/api/keywords', { word: newKeyword });
      }
      fetchKeywords();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving keyword:', error);
    }
  };

  const handleToggleActive = async (id, isActive) => {
    try {
      await axios.put(`/api/keywords/${id}`, { is_active: !isActive });
      fetchKeywords();
    } catch (error) {
      console.error('Error toggling keyword status:', error);
    }
  };

  const columns = [
    {
      field: 'word',
      headerName: 'คำค้นหา',
      flex: 1,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
    },
    {
      field: 'created_at',
      headerName: 'วันที่สร้าง',
      flex: 1,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      valueFormatter: (params) => {
        const date = new Date(params.value);
        return date.toLocaleString('th-TH');
      },
    },
    {
      field: 'is_active',
      headerName: 'สถานะ',
      width: 120,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      renderCell: (params) => (
        <Button
          variant={params.value ? 'contained' : 'outlined'}
          color={params.value ? 'primary' : 'secondary'}
          size="small"
          onClick={() => handleToggleActive(params.row.id, params.value)}
        >
          {params.value ? 'เปิดใช้งาน' : 'ปิดใช้งาน'}
        </Button>
      ),
    },
    {
      field: 'actions',
      headerName: 'จัดการ',
      width: 120,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      renderCell: (params) => (
        <Button
          variant="outlined"
          size="small"
          onClick={() => handleOpenDialog(params.row)}
        >
          แก้ไข
        </Button>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          จัดการคำค้นหา
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          เพิ่มคำค้นหา
        </Button>
      </Box>

      <DataGrid
        rows={keywords}
        columns={columns}
        pageSize={10}
        rowsPerPageOptions={[10, 25, 50]}
        autoHeight
        loading={loading}
        disableSelectionOnClick
        sx={{
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
          },
          '& .MuiDataGrid-columnHeaders': {
            bgcolor: 'background.paper',
            borderBottom: '2px solid rgba(0, 0, 0, 0.12)',
          },
        }}
      />

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          {editingKeyword ? 'แก้ไขคำค้นหา' : 'เพิ่มคำค้นหา'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="คำค้นหา"
            fullWidth
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>ยกเลิก</Button>
          <Button onClick={handleSubmit} variant="contained">
            บันทึก
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default KeywordManagement; 