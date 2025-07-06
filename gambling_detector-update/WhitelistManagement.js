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
  IconButton,
  Tooltip,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import axios from 'axios';

function WhitelistManagement() {
  const [whitelist, setWhitelist] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newNote, setNewNote] = useState('');
  const [editingItem, setEditingItem] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchWhitelist();
  }, []);

  const fetchWhitelist = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/whitelist');
      setWhitelist(response.data);
    } catch (error) {
      console.error('Error fetching whitelist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (item = null) => {
    setEditingItem(item);
    setNewUrl(item ? item.url : '');
    setNewNote(item ? item.note : '');
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewUrl('');
    setNewNote('');
    setEditingItem(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingItem) {
        await axios.put(`/api/whitelist/${editingItem.id}`, {
          url: newUrl,
          note: newNote,
        });
      } else {
        await axios.post('/api/whitelist', {
          url: newUrl,
          note: newNote,
        });
      }
      fetchWhitelist();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving whitelist item:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/api/whitelist/${id}`);
      fetchWhitelist();
    } catch (error) {
      console.error('Error deleting whitelist item:', error);
    }
  };

  const columns = [
    {
      field: 'url',
      headerName: 'URL',
      flex: 2,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
    },
    {
      field: 'note',
      headerName: 'หมายเหตุ',
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
      field: 'actions',
      headerName: 'จัดการ',
      width: 120,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      renderCell: (params) => (
        <Box>
          <Tooltip title="แก้ไข">
            <IconButton
              size="small"
              onClick={() => handleOpenDialog(params.row)}
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="ลบ">
            <IconButton
              size="small"
              onClick={() => handleDelete(params.row.id)}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          รายการอนุญาต
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          เพิ่ม URL
        </Button>
      </Box>

      <DataGrid
        rows={whitelist}
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
          {editingItem ? 'แก้ไข URL' : 'เพิ่ม URL'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="URL"
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            helperText="ใส่ URL แบบเต็ม เช่น https://example.com/path"
          />
          <TextField
            margin="dense"
            label="หมายเหตุ"
            fullWidth
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            multiline
            rows={2}
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

export default WhitelistManagement; 