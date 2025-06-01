import { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  TextField,
  InputAdornment,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

// Temporary mock data - will be replaced with actual API data
const mockReceipts = Array.from({ length: 50 }, (_, index) => ({
  id: index + 1,
  store: ['Biedronka', 'Lidl', 'Kaufland', 'Auchan'][Math.floor(Math.random() * 4)],
  date: new Date(2024, Math.floor(Math.random() * 3), Math.floor(Math.random() * 28) + 1).toLocaleDateString(),
  total: (Math.random() * 200 + 50).toFixed(2),
  items: Math.floor(Math.random() * 20) + 1,
}));

export default function ReceiptsList() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredReceipts = mockReceipts.filter(receipt =>
    receipt.store.toLowerCase().includes(searchTerm.toLowerCase()) ||
    receipt.date.includes(searchTerm) ||
    receipt.total.includes(searchTerm)
  );

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Paragony
      </Typography>

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Szukaj paragonów..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Sklep</TableCell>
              <TableCell>Data</TableCell>
              <TableCell align="right">Suma</TableCell>
              <TableCell align="right">Produkty</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredReceipts
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((receipt) => (
                <TableRow
                  key={receipt.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => {
                    // TODO: Navigate to receipt detail page
                    console.log(`Navigate to receipt ${receipt.id}`);
                  }}
                >
                  <TableCell>{receipt.id}</TableCell>
                  <TableCell>{receipt.store}</TableCell>
                  <TableCell>{receipt.date}</TableCell>
                  <TableCell align="right">${receipt.total}</TableCell>
                  <TableCell align="right">{receipt.items}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredReceipts.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
} 