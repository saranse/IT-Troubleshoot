import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  DragIndicator as DragIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import axios from 'axios';

function DomainManagement() {
  const [domains, setDomains] = useState([]);
  const [groups, setGroups] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('domain'); // 'domain' or 'group'
  const [newItemName, setNewItemName] = useState('');
  const [editingItem, setEditingItem] = useState(null);

  useEffect(() => {
    fetchDomains();
    fetchGroups();
  }, []);

  const fetchDomains = async () => {
    try {
      const response = await axios.get('/api/domains');
      setDomains(response.data);
    } catch (error) {
      console.error('Error fetching domains:', error);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await axios.get('/api/groups');
      setGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  const handleOpenDialog = (type, item = null) => {
    setDialogType(type);
    setEditingItem(item);
    setNewItemName(item ? item.name : '');
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewItemName('');
    setEditingItem(null);
  };

  const handleSubmit = async () => {
    try {
      if (dialogType === 'domain') {
        if (editingItem) {
          await axios.put(`/api/domains/${editingItem.id}`, { name: newItemName });
        } else {
          await axios.post('/api/domains', { name: newItemName });
        }
        fetchDomains();
      } else {
        if (editingItem) {
          await axios.put(`/api/groups/${editingItem.id}`, { name: newItemName });
        } else {
          await axios.post('/api/groups', { name: newItemName });
        }
        fetchGroups();
      }
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving item:', error);
    }
  };

  const handleDelete = async (type, id) => {
    try {
      if (type === 'domain') {
        await axios.delete(`/api/domains/${id}`);
        fetchDomains();
      } else {
        await axios.delete(`/api/groups/${id}`);
        fetchGroups();
      }
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const handleDragEnd = async (result) => {
    if (!result.destination) return;

    const sourceGroupId = result.source.droppableId;
    const destinationGroupId = result.destination.droppableId;
    const domainId = result.draggableId;

    try {
      await axios.post('/api/groups/move-domain', {
        domain_id: domainId,
        new_group_id: destinationGroupId,
      });
      fetchGroups();
    } catch (error) {
      console.error('Error moving domain:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          จัดการโดเมน
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog('group')}
          >
            เพิ่มกลุ่ม
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog('domain')}
          >
            เพิ่มโดเมน
          </Button>
        </Box>
      </Box>

      <DragDropContext onDragEnd={handleDragEnd}>
        <Grid container spacing={3}>
          {groups.map((group) => (
            <Grid item xs={12} sm={6} md={4} key={group.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6">{group.name}</Typography>
                    <Box>
                      <Tooltip title="แก้ไข">
                        <IconButton size="small" onClick={() => handleOpenDialog('group', group)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="ลบ">
                        <IconButton size="small" onClick={() => handleDelete('group', group.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  <Droppable droppableId={group.id.toString()}>
                    {(provided) => (
                      <Box
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        sx={{ minHeight: 100 }}
                      >
                        {group.domains.map((domain, index) => (
                          <Draggable
                            key={domain.id}
                            draggableId={domain.id.toString()}
                            index={index}
                          >
                            {(provided) => (
                              <Box
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                sx={{
                                  p: 1,
                                  mb: 1,
                                  bgcolor: 'background.default',
                                  borderRadius: 1,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Box {...provided.dragHandleProps}>
                                    <DragIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                  </Box>
                                  <Typography>{domain.name}</Typography>
                                </Box>
                                <Box>
                                  <Tooltip title="แก้ไข">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleOpenDialog('domain', domain)}
                                    >
                                      <EditIcon />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="ลบ">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleDelete('domain', domain.id)}
                                    >
                                      <DeleteIcon />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              </Box>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </Box>
                    )}
                  </Droppable>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </DragDropContext>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          {editingItem
            ? `แก้ไข${dialogType === 'domain' ? 'โดเมน' : 'กลุ่ม'}`
            : `เพิ่ม${dialogType === 'domain' ? 'โดเมน' : 'กลุ่ม'}`}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={dialogType === 'domain' ? 'ชื่อโดเมน' : 'ชื่อกลุ่ม'}
            fullWidth
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
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

export default DomainManagement; 