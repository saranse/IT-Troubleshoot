import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  MenuItem,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  FileDownload as ExportIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import thLocale from 'date-fns/locale/th';
import axios from 'axios';

function ScanHistory() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    domain: '',
    keyword: '',
  });
  const [selectedResult, setSelectedResult] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: filters.startDate?.toISOString(),
        end_date: filters.endDate?.toISOString(),
        domain: filters.domain || undefined,
        keyword: filters.keyword || undefined,
      };
      const response = await axios.get('/api/results', { params });
      setResults(response.data);
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get('/api/results/export', {
        params: {
          start_date: filters.startDate?.toISOString(),
          end_date: filters.endDate?.toISOString(),
          domain: filters.domain || undefined,
          keyword: filters.keyword || undefined,
        },
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan-results-${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting results:', error);
    }
  };

  const handleViewDetails = (result) => {
    setSelectedResult(result);
    setOpenDialog(true);
  };

  const columns = [
    {
      field: 'domain',
      headerName: 'โดเมน',
      flex: 1,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      valueGetter: (params) => params.row.domain.name,
    },
    {
      field: 'keyword',
      headerName: 'คำที่พบ',
      flex: 1,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
    },
    {
      field: 'url',
      headerName: 'URL',
      flex: 2,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      renderCell: (params) => (
        <Typography
          component="a"
          href={params.value}
          target="_blank"
          rel="noopener noreferrer"
          color="primary"
          sx={{ textDecoration: 'none' }}
        >
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'created_at',
      headerName: 'วันที่พบ',
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
      width: 100,
      renderHeader: (params) => (
        <Typography fontWeight="bold">{params.colDef.headerName}</Typography>
      ),
      renderCell: (params) => (
        <Tooltip title="ดูรายละเอียด">
          <IconButton
            size="small"
            onClick={() => handleViewDetails(params.row)}
          >
            <ViewIcon />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          ประวัติการค้นหา
        </Typography>
        <Button
          variant="contained"
          startIcon={<ExportIcon />}
          onClick={handleExport}
        >
          ส่งออก
        </Button>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={thLocale}>
              <DatePicker
                label="วันที่เริ่มต้น"
                value={filters.startDate}
                onChange={(date) => setFilters({ ...filters, startDate: date })}
                renderInput={(params) => <TextField {...params} />}
              />
              <DatePicker
                label="วันที่สิ้นสุด"
                value={filters.endDate}
                onChange={(date) => setFilters({ ...filters, endDate: date })}
                renderInput={(params) => <TextField {...params} />}
              />
            </LocalizationProvider>
            <TextField
              label="โดเมน"
              value={filters.domain}
              onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
            />
            <TextField
              label="คำค้นหา"
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
            />
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={fetchResults}
              sx={{ height: 56 }}
            >
              ค้นหา
            </Button>
          </Box>
        </CardContent>
      </Card>

      <DataGrid
        rows={results}
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

      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>รายละเอียดผลการค้นหา</DialogTitle>
        <DialogContent>
          {selectedResult && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                <strong>โดเมน:</strong> {selectedResult.domain.name}
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                <strong>URL:</strong>{' '}
                <Typography
                  component="a"
                  href={selectedResult.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  color="primary"
                >
                  {selectedResult.url}
                </Typography>
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                <strong>คำที่พบ:</strong> {selectedResult.keyword}
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                <strong>บริบท:</strong>
              </Typography>
              {Object.entries(JSON.parse(selectedResult.matches)).map(([keyword, contexts]) => (
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
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default ScanHistory; 