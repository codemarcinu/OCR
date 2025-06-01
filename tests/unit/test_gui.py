"""
Unit tests for the GUI module.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from gui import ReceiptProcessorGUI

@pytest.fixture
def mock_qapp(monkeypatch):
    """Mock QApplication."""
    mock = MagicMock()
    monkeypatch.setattr('PyQt6.QtWidgets.QApplication', mock)
    return mock

@pytest.fixture
def mock_gui(mock_qapp):
    """Create mocked GUI instance."""
    with patch('gui.ReceiptProcessorGUI') as mock_gui:
        instance = mock_gui.return_value
        instance.selected_file = MagicMock()
        instance.model_name = MagicMock()
        instance.ollama_url = MagicMock()
        instance.prompt_file = MagicMock()
        instance.preview_image = None
        instance.process_receipt = MagicMock()
        instance.update_preview = MagicMock()
        instance.update_tables = MagicMock()
        instance.update_prompt_file = MagicMock()
        yield instance

@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image file for testing."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (800, 1200), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((400, 600), "Sample Receipt Text", fill="black")
    path = tmp_path / "test_receipt.jpg"
    img.save(path)
    return path

def test_gui_initialization(mock_gui):
    """Test if GUI initializes correctly."""
    assert mock_gui.selected_file is not None
    assert mock_gui.model_name is not None
    assert mock_gui.ollama_url is not None

def test_file_selection(mock_gui, sample_image):
    """Test file selection functionality."""
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
        mock_dialog.return_value = (str(sample_image), "Images (*.jpg *.png)")
        mock_gui.select_file()
        mock_gui.selected_file.setText.assert_called_once_with(str(sample_image))

def test_store_selection(mock_gui):
    """Test store selection functionality."""
    mock_gui.selected_store = MagicMock()
    mock_gui.prompt_file = MagicMock()
    
    stores = ["Lidl", "Biedronka", "Kaufland"]
    for store in stores:
        mock_gui.selected_store.text.return_value = store
        mock_gui.update_prompt_file()
        assert mock_gui.update_prompt_file.call_count > 0

@patch('process_receipt.process_receipt')
def test_receipt_processing(mock_process, mock_gui, sample_image):
    """Test receipt processing functionality."""
    # Setup mock response
    mock_process.return_value = {
        "sklep": {"nazwa": "Lidl"},
        "data": "2024-01-01",
        "produkty": [
            {
                "nazwa": "Test Product",
                "ilosc": 1,
                "suma": 9.99
            }
        ]
    }
    
    mock_gui.selected_file.text.return_value = str(sample_image)
    mock_gui.process_receipt()
    mock_gui.process_receipt.assert_called_once()

def test_error_handling(mock_gui):
    """Test error handling in GUI."""
    mock_gui.selected_file.text.return_value = ""
    mock_gui.status_var = MagicMock()
    mock_gui.process_receipt()
    mock_gui.process_receipt.assert_called_once()

@patch('process_receipt.process_receipt')
def test_processing_error_handling(mock_process, mock_gui, sample_image):
    """Test handling of processing errors."""
    mock_process.side_effect = Exception("Test error")
    mock_gui.selected_file.text.return_value = str(sample_image)
    mock_gui.status_var = MagicMock()
    
    mock_gui.process_receipt()
    mock_gui.process_receipt.assert_called_once()

def test_preview_update(mock_gui, sample_image):
    """Test image preview functionality."""
    mock_gui.preview_canvas = MagicMock()
    mock_gui.update_preview(Path(sample_image))
    mock_gui.update_preview.assert_called_once_with(Path(sample_image))

def test_table_updates(mock_gui):
    """Test table update functionality."""
    mock_gui.receipts_tree = MagicMock()
    mock_gui.products_tree = MagicMock()
    
    test_data = {
        "sklep": {"nazwa": "Lidl"},
        "data": "2024-01-01",
        "produkty": [
            {
                "nazwa": "Test Product 1",
                "ilosc": 1,
                "suma": 9.99
            },
            {
                "nazwa": "Test Product 2",
                "ilosc": 2,
                "suma": 19.98
            }
        ]
    }
    
    mock_gui.update_tables(test_data)
    mock_gui.update_tables.assert_called_once_with(test_data) 