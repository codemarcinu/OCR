import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

// Temporary mock data - will be replaced with actual API data
const mockInventory = Array.from({ length: 50 }, (_, index) => ({
  id: index + 1,
  name: ['Mleko', 'Chleb', 'Jajka', 'Pomidory', 'Ser', 'Kurczak', 'Ryż'][
    Math.floor(Math.random() * 7)
  ],
  category: ['Nabiał', 'Pieczywo', 'Warzywa', 'Mięso', 'Zboża'][
    Math.floor(Math.random() * 5)
  ],
  quantity: Math.floor(Math.random() * 100),
  averagePrice: (Math.random() * 20 + 5).toFixed(2),
  lastPurchased: new Date(
    2024,
    Math.floor(Math.random() * 3),
    Math.floor(Math.random() * 28) + 1
  ).toLocaleDateString(),
  status: ['W magazynie', 'Mało', 'Brak'][
    Math.floor(Math.random() * 3)
  ],
}));

const categories = ['Wszystkie', 'Nabiał', 'Pieczywo', 'Warzywa', 'Mięso', 'Zboża'];

export default function InventoryView() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Wszystkie');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'W magazynie':
        return 'success';
      case 'Mało':
        return 'warning';
      case 'Brak':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredInventory = mockInventory.filter(
    (item) =>
      (item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.category.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (selectedCategory === 'Wszystkie' || item.category === selectedCategory)
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
        Stan magazynowy
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          sx={{ flex: 1 }}
          variant="outlined"
          placeholder="Szukaj produktów..."
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
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Kategoria</InputLabel>
          <Select
            value={selectedCategory}
            label="Kategoria"
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map((category) => (
              <MenuItem key={category} value={category}>
                {category}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nazwa</TableCell>
              <TableCell>Kategoria</TableCell>
              <TableCell align="right">Ilość</TableCell>
              <TableCell align="right">Średnia cena</TableCell>
              <TableCell>Ostatni zakup</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredInventory
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell align="right">{item.quantity}</TableCell>
                  <TableCell align="right">${item.averagePrice}</TableCell>
                  <TableCell>{item.lastPurchased}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
                      color={getStatusColor(item.status) as any}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredInventory.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
} 