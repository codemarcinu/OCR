import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';

// Temporary mock data - will be replaced with actual API data
const mockCategories = [
  {
    id: 1,
    name: 'Nabiał',
    description: 'Mleko, ser, jogurt i inne produkty mleczne',
    itemCount: 45,
  },
  {
    id: 2,
    name: 'Pieczywo',
    description: 'Chleb, bułki i wyroby piekarnicze',
    itemCount: 32,
  },
  {
    id: 3,
    name: 'Warzywa',
    description: 'Świeże warzywa i zielenina',
    itemCount: 67,
  },
  {
    id: 4,
    name: 'Owoce',
    description: 'Świeże owoce i jagody',
    itemCount: 54,
  },
  {
    id: 5,
    name: 'Mięso',
    description: 'Świeże mięso i drób',
    itemCount: 28,
  },
];

interface CategoryDialogProps {
  open: boolean;
  onClose: () => void;
  category?: typeof mockCategories[0];
  onSave: (category: Omit<typeof mockCategories[0], 'itemCount'>) => void;
}

function CategoryDialog({ open, onClose, category, onSave }: CategoryDialogProps) {
  const [editedCategory, setEditedCategory] = useState(
    category
      ? { id: category.id, name: category.name, description: category.description }
      : {
          id: Date.now(),
          name: '',
          description: '',
        }
  );

  const handleSave = () => {
    onSave(editedCategory);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{category ? 'Edytuj kategorię' : 'Dodaj kategorię'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Nazwa"
            value={editedCategory.name}
            onChange={(e) =>
              setEditedCategory({ ...editedCategory, name: e.target.value })
            }
          />
          <TextField
            label="Opis"
            multiline
            rows={3}
            value={editedCategory.description}
            onChange={(e) =>
              setEditedCategory({
                ...editedCategory,
                description: e.target.value,
              })
            }
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

export default function ProductCategories() {
  const [categories, setCategories] = useState(mockCategories);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentCategory, setCurrentCategory] = useState<
    typeof mockCategories[0] | undefined
  >();

  const handleEditCategory = (category: typeof mockCategories[0]) => {
    setCurrentCategory(category);
    setDialogOpen(true);
  };

  const handleAddCategory = () => {
    setCurrentCategory(undefined);
    setDialogOpen(true);
  };

  const handleDeleteCategory = (categoryId: number) => {
    setCategories(categories.filter((cat) => cat.id !== categoryId));
  };

  const handleSaveCategory = (
    editedCategory: Omit<typeof mockCategories[0], 'itemCount'>
  ) => {
    if (currentCategory) {
      setCategories(
        categories.map((cat) =>
          cat.id === currentCategory.id
            ? { ...editedCategory, itemCount: cat.itemCount }
            : cat
        )
      );
    } else {
      setCategories([...categories, { ...editedCategory, itemCount: 0 }]);
    }
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Typography variant="h4">Kategorie produktów</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddCategory}
        >
          Dodaj kategorię
        </Button>
      </Box>

      <Paper>
        <List>
          {categories.map((category) => (
            <ListItem key={category.id} divider>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {category.name}
                    <Chip
                      size="small"
                      label={`${category.itemCount} produktów`}
                      color="primary"
                    />
                  </Box>
                }
                secondary={category.description}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="edit"
                  onClick={() => handleEditCategory(category)}
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDeleteCategory(category.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Paper>

      <CategoryDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        category={currentCategory}
        onSave={handleSaveCategory}
      />
    </Box>
  );
} 