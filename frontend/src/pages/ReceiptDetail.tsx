import { useState } from 'react';
import { useParams } from 'react-router-dom';
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
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';

// Temporary mock data - will be replaced with actual API data
const mockReceipt = {
  id: 1,
  store: 'Biedronka',
  date: '2024-03-15',
  total: 156.78,
  items: [
    { id: 1, name: 'Milk', quantity: 2, price: 3.99, category: 'Dairy' },
    { id: 2, name: 'Bread', quantity: 1, price: 4.50, category: 'Bakery' },
    { id: 3, name: 'Eggs', quantity: 1, price: 8.99, category: 'Dairy' },
    { id: 4, name: 'Tomatoes', quantity: 0.5, price: 5.99, category: 'Vegetables' },
  ],
};

interface EditItemDialogProps {
  open: boolean;
  onClose: () => void;
  item?: typeof mockReceipt.items[0];
  onSave: (item: typeof mockReceipt.items[0]) => void;
}

function EditItemDialog({ open, onClose, item, onSave }: EditItemDialogProps) {
  const [editedItem, setEditedItem] = useState(item || {
    id: Date.now(),
    name: '',
    quantity: 1,
    price: 0,
    category: '',
  });

  const handleSave = () => {
    onSave(editedItem);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{item ? 'Edytuj produkt' : 'Dodaj produkt'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Nazwa"
            value={editedItem.name}
            onChange={(e) => setEditedItem({ ...editedItem, name: e.target.value })}
          />
          <TextField
            label="Ilość"
            type="number"
            value={editedItem.quantity}
            onChange={(e) => setEditedItem({ ...editedItem, quantity: parseFloat(e.target.value) })}
          />
          <TextField
            label="Cena"
            type="number"
            value={editedItem.price}
            onChange={(e) => setEditedItem({ ...editedItem, price: parseFloat(e.target.value) })}
          />
          <TextField
            label="Kategoria"
            value={editedItem.category}
            onChange={(e) => setEditedItem({ ...editedItem, category: e.target.value })}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Anuluj</Button>
        <Button onClick={handleSave} variant="contained">
          Zapisz
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function ReceiptDetail() {
  const { id } = useParams<{ id: string }>();
  const [items, setItems] = useState(mockReceipt.items);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<typeof mockReceipt.items[0] | undefined>();

  const handleEditItem = (item: typeof mockReceipt.items[0]) => {
    setCurrentItem(item);
    setEditDialogOpen(true);
  };

  const handleAddItem = () => {
    setCurrentItem(undefined);
    setEditDialogOpen(true);
  };

  const handleDeleteItem = (itemId: number) => {
    setItems(items.filter((item) => item.id !== itemId));
  };

  const handleSaveItem = (editedItem: typeof mockReceipt.items[0]) => {
    if (currentItem) {
      setItems(items.map((item) => (item.id === currentItem.id ? editedItem : item)));
    } else {
      setItems([...items, editedItem]);
    }
  };

  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Szczegóły paragonu
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Informacje o paragonie
        </Typography>
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Box>
            <Typography color="text.secondary">Sklep</Typography>
            <Typography>{mockReceipt.store}</Typography>
          </Box>
          <Box>
            <Typography color="text.secondary">Data</Typography>
            <Typography>{mockReceipt.date}</Typography>
          </Box>
          <Box>
            <Typography color="text.secondary">Suma</Typography>
            <Typography>${total.toFixed(2)}</Typography>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Produkty</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddItem}
        >
          Dodaj produkt
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nazwa</TableCell>
              <TableCell>Kategoria</TableCell>
              <TableCell align="right">Ilość</TableCell>
              <TableCell align="right">Cena</TableCell>
              <TableCell align="right">Suma</TableCell>
              <TableCell align="right">Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.name}</TableCell>
                <TableCell>{item.category}</TableCell>
                <TableCell align="right">{item.quantity}</TableCell>
                <TableCell align="right">${item.price.toFixed(2)}</TableCell>
                <TableCell align="right">
                  ${(item.price * item.quantity).toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleEditItem(item)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteItem(item.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <EditItemDialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        item={currentItem}
        onSave={handleSaveItem}
      />
    </Box>
  );
} 