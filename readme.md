# Similar Image Finder

A simple desktop application for finding similar and duplicate images using advanced perceptual hashing algorithms. Built with Python and PySide6, this tool helps you organize your image library by detecting visually similar images across your file system.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## Features

- 🔍 **Perceptual Image Hashing**: Uses advanced DCT-based color hashing for accurate similarity detection
- 🎨 **Color-Aware Processing**: Analyzes all RGB channels for higher accuracy
- ⚡ **Fast Search**: Efficient caching system for quick lookups
- 🎯 **Adjustable Sensitivity**: Real-time threshold control with slider and spinbox
- 📊 **Visual Results**: Displays thumbnails, similarity percentages, and file information
- 🌓 **Dark Theme**: Modern, eye-friendly interface
- 💾 **Smart Caching**: Persistent cache with file modification tracking
- 🖼️ **Multiple Formats**: Supports JPG, PNG, BMP, GIF, WebP, and TIFF

## Screenshots

The application features:
- Clean sidebar with cache management and sensitivity controls
- Source image preview panel
- Scrollable results with similarity metrics
- One-click file opening

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended for large image libraries)
- **Storage**: Depends on your image library size

### Required Python Packages

```bash
# Core dependencies
PySide6>=6.5.0          # Qt6 GUI framework
Pillow>=10.0.0          # Image processing
numpy>=1.24.0           # Numerical operations
scipy>=1.10.0           # Scientific computing (for DCT)
```

## Installation

### 1. Clone or Download

```bash
# Clone the repository
git clone https://github.com/yourusername/similar-image-finder.git
cd similar-image-finder

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install PySide6 Pillow numpy scipy
```

## Usage

### Starting the Application

```bash
# Make sure virtual environment is activated
python app.py
```

### First-Time Setup

1. **Sync Cache**: Click "Sync Cache" button to build the initial image database
   - Default search path: `~/Pictures` (Your Pictures folder)
   - This process may take several minutes depending on library size
   - Progress is displayed in the sidebar

2. **Upload Image**: Click "Upload Image" to select a source image
   - Supported formats: JPG, JPEG, PNG, BMP, GIF, WebP

3. **Adjust Sensitivity**: Use the slider to control similarity threshold
   - **1-100**: similarity percentage

4. **Browse Results**: Scroll through similar images
   - View similarity percentage and file size
   - Click "Open" to view full image in default viewer

### Understanding Results

- **Distance**: Hamming distance between image hashes (lower = more similar)
- **Similarity %**: Percentage-based similarity metric (higher = more similar)
- **Color Coding**:
  - 🟢 Green (Distance > 95%): Nearly identical
  - 🟡 Yellow (Distance > 85%): Very similar
  - 🟠 Orange (Distance > 75%): Somewhat similar
  - 🔴 Red (Distance < 75%): Loosely similar

## How It Works

### Perceptual Hashing Algorithm

The application uses a color-aware perceptual hash based on:

1. **Color Channel Processing**: Analyzes RGB channels separately
2. **DCT Transform**: Applies Discrete Cosine Transform to extract frequency features
3. **Low-Frequency Analysis**: Focuses on perceptual content (ignoring minor details)
4. **Binary Hash Generation**: Creates compact hash for fast comparison
5. **Hamming Distance**: Measures similarity by counting differing bits

### Advantages Over Simple Methods

- ✅ Resilient to minor edits (brightness, contrast, compression)
- ✅ Detects similar images even with different resolutions
- ✅ Color-aware for better accuracy
- ✅ Fast comparison using bit operations
- ✅ Small memory footprint

## Configuration

### Changing Search Paths

Edit the `__init__` method in `ImageFinder` class:

```python
self.search_paths = [
    str(Path.home() / 'Pictures'),
    str(Path.home() / 'Downloads'),
    '/path/to/custom/folder'
]
```

### Adjusting Hash Size

In `ImageHasher.calculate_hash()`:

```python
def calculate_hash(image_path, hash_size=32):  # Change this value
    # Larger = more detailed (slower)
    # Smaller = faster (less detailed)
```

### Cache Location

The cache file is stored at:
- **Windows**: `C:\Users\YourName\.image_finder_cache.json`
- **macOS/Linux**: `~/.image_finder_cache.json`

## Troubleshooting

### "Cache: Does not exist"
- Click "Sync Cache" to build the initial database
- Ensure search paths are accessible

### "No similar images found"
- Try increasing the threshold slider
- Verify cache contains images (check cache count in sidebar)
- Re-sync cache if files were added recently

### Slow Performance
- Reduce hash_size for faster processing
- Use SSD for cache storage
- Limit search paths to specific folders

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade PySide6 Pillow numpy scipy
```

## Advanced Features

### Batch Processing

To process multiple source images, modify the code to iterate through a folder:

```python
for img_file in Path('source_folder').glob('*.jpg'):
    self.process_image(str(img_file))
```

### Export Results

Add export functionality by saving `self.similar_images` to CSV or JSON:

```python
import csv

with open('results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['path', 'distance', 'size'])
    writer.writeheader()
    writer.writerows(self.similar_images)
```

## Performance Tips

- **Cache Regularly**: Re-sync after adding many new images
- **Optimize Search Paths**: Only include relevant folders
- **Clean Cache**: Delete cache file to start fresh if corrupted
- **Hardware**: Use SSD and sufficient RAM for large libraries

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Multi-threaded image processing
- [ ] Additional hash algorithms (aHash, wHash)
- [ ] Duplicate deletion functionality
- [ ] Drag-and-drop image upload
- [ ] Custom search path UI
- [ ] Progress pause/resume
- [ ] Image preview on hover

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- **PySide6**: Qt framework for Python
- **Pillow**: Python Imaging Library
- **SciPy**: Scientific computing tools
- **NumPy**: Numerical computing library

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: your.email@example.com

---

**Made with ❤️ for organizing image libraries**