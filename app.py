import sys, os, json
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.fftpack import dct
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFileDialog, QScrollArea, QProgressBar, QMessageBox, QSlider, QSpinBox
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont

class ImageHasher:
    @staticmethod
    def calculate_hash(image_path, hash_size=32):
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            image = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
            pixels = np.array(image, dtype=np.float32)

            hash_parts = []
            for channel in range(3):
                channel_data = pixels[:, :, channel]
                dct_data = dct(dct(channel_data, axis=0), axis=1)
                dct_low = dct_data[:hash_size//4, :hash_size//4]
                median = np.median(dct_low)
                diff = dct_low > median
                hash_parts.append(diff.flatten())

            combined_hash = np.concatenate(hash_parts)
            hash_array = np.packbits(combined_hash)
            hash_string = ''.join(f'{byte:02x}' for byte in hash_array)

            return hash_string
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None

    @staticmethod
    def hamming_distance(hash1, hash2):
        if len(hash1) != len(hash2):
            return 0

        different_bits = 0
        total_bits = len(hash1) * 4

        for h1, h2 in zip(hash1, hash2):
            xor_result = int(h1, 16) ^ int(h2, 16)
            different_bits += bin(xor_result).count('1')

        similarity_percentage = ((total_bits - different_bits) / total_bits) * 100

        return round(similarity_percentage, 2)

class CacheBuilder(QThread):
    progress = Signal(int, int, str)
    finished = Signal()

    def __init__(self, search_paths, cache_path):
        super().__init__()
        self.search_paths = search_paths
        self.cache_path = cache_path
        self.is_running = True

    def run(self):
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
        cache_data = {}
        all_images = []
        for search_path in self.search_paths:
            path = Path(search_path)
            if not path.exists():
                continue

            for ext in image_extensions:
                all_images.extend(path.rglob(f'*{ext}'))
                all_images.extend(path.rglob(f'*{ext.upper()}'))

        total = len(all_images)
        self.progress.emit(0, total, "Scanning images...")

        for idx, img_path in enumerate(all_images):
            if not self.is_running:
                break

            try:
                img_hash = ImageHasher.calculate_hash(img_path)
                if img_hash is not None:
                    file_stats = os.stat(img_path)
                    cache_data[str(img_path)] = {
                        'hash': img_hash,
                        'size': file_stats.st_size,
                        'modified': file_stats.st_mtime
                    }

                self.progress.emit(idx + 1, total, f"Processed: {idx + 1}/{total}")
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue

        if self.is_running:
            try:
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                self.progress.emit(total, total, "Cache saved successfully!")
            except Exception as e:
                print(f"Error saving cache: {e}")

        self.finished.emit()

    def stop(self):
        self.is_running = False

class ImageFinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Similar Image Finder")
        self.showMaximized()
        
        self.cache_path = Path.home() / '.image_finder_cache.json'
        self.search_paths = [str(Path.home() / 'Pictures')]
        self.cache_data = {}
        self.current_image_hash = None
        self.similar_images = []
        self.current_threshold = 90

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_sidebar(main_layout)
        self.create_main_section(main_layout)
        self.load_cache()

    def create_sidebar(self, parent_layout):
        sidebar = QWidget()
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #212121;
                border-right: 1px solid #757575;
                min-width: 250px;
                max-width: 250px;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        title = QLabel("Similar Image Finder")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; padding: 5px; min-width: 230px; max-width: 230px;")
        sidebar_layout.addWidget(title)

        self.cache_info_label = QLabel("Cache: Loading...")
        self.cache_info_label.setWordWrap(True)
        self.cache_info_label.setStyleSheet("color: white; padding: 5px; font-size: 14px; min-width: 230px; max-width: 230px;")
        sidebar_layout.addWidget(self.cache_info_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #424242;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #212121;
                min-width: 230px;
                max-width: 230px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.progress_bar.setVisible(False)
        sidebar_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("color: white; padding: 5px; font-size: 12px; min-width: 230px; max-width: 230px;")
        self.progress_label.setVisible(False)
        sidebar_layout.addWidget(self.progress_label)
        
        sensitivity_label = QLabel("Sensitivity:")
        sensitivity_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold; padding: 5px; min-width: 230px; max-width: 230px;")
        sidebar_layout.addWidget(sensitivity_label)
        
        sensitivity_container = QWidget()
        sensitivity_container.setStyleSheet("min-width: 240px; max-width: 240px;")
        sensitivity_layout = QVBoxLayout(sensitivity_container)
        sensitivity_layout.setContentsMargins(0, 0, 0, 0)
        sensitivity_layout.setSpacing(5)
        
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(1)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(self.current_threshold)
        self.sensitivity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #424242;
                height: 8px;
                background: #2a2a2a;
                border-radius: 4px;
                min-width: 230px;
                max-width: 230px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
                min-width: 18px;
                max-width: 18px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 4px;
                min-width: 230px;
                max-width: 230px;
            }
        """)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        spinbox_container = QWidget()
        spinbox_layout = QHBoxLayout(spinbox_container)
        spinbox_layout.setContentsMargins(0, 0, 0, 0)
        spinbox_layout.setSpacing(5)
        
        spinbox_label = QLabel("Threshold:")
        spinbox_label.setStyleSheet("color: #999999; font-size: 11px; min-width: 60px; max-width: 60px;")
        spinbox_layout.addWidget(spinbox_label)
        
        self.sensitivity_spinbox = QSpinBox()
        self.sensitivity_spinbox.setMinimum(1)
        self.sensitivity_spinbox.setMaximum(100)
        self.sensitivity_spinbox.setValue(self.current_threshold)
        self.sensitivity_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #424242;
                color: white;
                border: 1px solid #757575;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
                min-width: 60px;
                max-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #636363;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #757575;
            }
        """)
        self.sensitivity_spinbox.valueChanged.connect(self.on_spinbox_changed)
        spinbox_layout.addWidget(self.sensitivity_spinbox)
        spinbox_layout.addStretch()
        
        sensitivity_layout.addWidget(spinbox_container)
        
        # به‌روزرسانی راهنما با سیستم درصدی
        self.help_label = QLabel()
        self.help_label.setStyleSheet("color: #757575; font-size: 12px; min-width: 240px; max-width: 240px;")
        self.help_label.setWordWrap(True)
        self.update_help_label()
        sensitivity_layout.addWidget(self.help_label)
        
        sidebar_layout.addWidget(sensitivity_container)
        
        sidebar_layout.addStretch()

        btn_load = QPushButton("Upload Image")
        btn_load.setStyleSheet(self.button_style())
        btn_load.clicked.connect(self.load_image)
        sidebar_layout.addWidget(btn_load)

        self.btn_sync = QPushButton("Sync Cache")
        self.btn_sync.setStyleSheet(self.button_style())
        self.btn_sync.clicked.connect(self.sync_cache)
        sidebar_layout.addWidget(self.btn_sync)

        btn_exit = QPushButton("Exit")
        btn_exit.setStyleSheet(self.button_style())
        btn_exit.clicked.connect(self.close)
        sidebar_layout.addWidget(btn_exit)

        parent_layout.addWidget(sidebar)
    
    def update_help_label(self):
        self.help_label.setText(f"Current: ≥{self.current_threshold}%")
    
    def on_sensitivity_changed(self, value):
        self.sensitivity_spinbox.blockSignals(True)
        self.sensitivity_spinbox.setValue(value)
        self.sensitivity_spinbox.blockSignals(False)
        self.current_threshold = value
        self.update_help_label()

        if self.current_image_hash is not None and self.cache_data:
            self.find_similar_images()

    def on_spinbox_changed(self, value):
        self.sensitivity_slider.blockSignals(True)
        self.sensitivity_slider.setValue(value)
        self.sensitivity_slider.blockSignals(False)
        self.current_threshold = value
        self.update_help_label()

        if self.current_image_hash is not None and self.cache_data:
            self.find_similar_images()
    
    def button_style(self):
        return """
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 8px;
                font-weight: bold;
                min-width: 200px;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #636363;
            }
            QPushButton:pressed {
                background-color: #636363;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """

    def create_main_section(self, parent_layout):
        main_section = QWidget()
        main_section.setStyleSheet("background-color: #212121;")

        main_layout = QVBoxLayout(main_section)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        source_label = QLabel("Source Image:")
        source_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(source_label)

        self.source_image_label = QLabel()
        self.source_image_label.setAlignment(Qt.AlignCenter)
        self.source_image_label.setStyleSheet("""
            background-color: #2a2a2a; 
            border: 2px dashed #757575;
            border-radius: 10px;
            color: #999999;
            font-size: 14px;
            min-height: 200px;
            max-height: 300px;
        """)
        self.source_image_label.setText("No image uploaded\nClick 'Upload Image' to get started")
        main_layout.addWidget(self.source_image_label)

        similar_label = QLabel("Similar Images:")
        similar_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(similar_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2a2a2a;
                border: 2px solid #424242;
                border-radius: 10px;
            }
        """)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(10)

        self.scroll_area.setWidget(self.results_widget)
        main_layout.addWidget(self.scroll_area)

        parent_layout.addWidget(main_section, stretch=1)
    
    def load_cache(self):
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                self.update_cache_info()
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.cache_data = {}
                self.cache_info_label.setText("Cache: Error loading cache\nPlease sync again")
        else:
            self.cache_info_label.setText("Cache: Does not exist\nPlease sync")
    
    def update_cache_info(self):
        count = len(self.cache_data)
        self.cache_info_label.setText(f"Cache: {count:,} images")
    
    def sync_cache(self):
        reply = QMessageBox.question(
            self,
            'Sync Cache',
            f'Do you want to sync the cache?\nSearch paths: {", ".join(self.search_paths)}\n\nThis may take some time.',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.start_cache_building()
    
    def start_cache_building(self):
        self.btn_sync.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.cache_builder = CacheBuilder(self.search_paths, self.cache_path)
        self.cache_builder.progress.connect(self.update_progress)
        self.cache_builder.finished.connect(self.cache_build_finished)
        self.cache_builder.start()

    def update_progress(self, current, total, message):
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def cache_build_finished(self):
        self.load_cache()
        self.btn_sync.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        QMessageBox.information(
            self,
            'Sync Complete',
            f'Cache built successfully!\n{len(self.cache_data):,} images processed.'
        )

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"
        )

        if file_path:
            self.process_image(file_path)
    
    def process_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.source_image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.source_image_label.setPixmap(scaled_pixmap)

        self.current_image_hash = ImageHasher.calculate_hash(image_path)
        
        if self.current_image_hash is None:
            QMessageBox.warning(self, 'Error', 'Could not calculate image hash')
            return

        if not self.cache_data:
            QMessageBox.warning(
                self,
                'Empty Cache',
                'Please sync the cache first'
            )
            return

        self.find_similar_images()

    def find_similar_images(self):
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.similar_images = []
        for img_path, data in self.cache_data.items():
            img_hash = data.get('hash')
            similarity = ImageHasher.hamming_distance(self.current_image_hash, img_hash)

            if similarity >= self.current_threshold:
                self.similar_images.append({
                    'path': img_path,
                    'similarity': similarity,
                    'size': data.get('size', 0)
                })

        self.similar_images.sort(key=lambda x: x['similarity'], reverse=True)

        if self.similar_images:
            for item in self.similar_images[:50]:
                self.add_result_item(item)

            summary = QLabel(f"Total similar images: {len(self.similar_images)} (showing top {min(50, len(self.similar_images))})")
            summary.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold; padding: 10px;")
            self.results_layout.addWidget(summary)
        else:
            no_result = QLabel(f"No similar images found with ≥{self.current_threshold}% similarity\nTry increasing the threshold slider")
            no_result.setStyleSheet("color: #999999; font-size: 14px; padding: 20px;")
            no_result.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(no_result)

        self.results_layout.addStretch()
        self.scroll_area.verticalScrollBar().setValue(0)

    def add_result_item(self, item):
        result_widget = QWidget()
        result_widget.setStyleSheet("""
            QWidget {
                background-color: #333333;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        result_layout = QHBoxLayout(result_widget)
        result_layout.setContentsMargins(10, 10, 10, 10)

        thumbnail = QLabel()
        thumbnail.setFixedSize(100, 100)
        thumbnail.setStyleSheet("background-color: #2a2a2a; border-radius: 5px;")
        pixmap = QPixmap(item['path'])
        if not pixmap.isNull():
            scaled = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumbnail.setPixmap(scaled)

        result_layout.addWidget(thumbnail)

        info_layout = QVBoxLayout()
        path_label = QLabel(f"Path: {item['path']}")
        path_label.setStyleSheet("color: white; font-size: 12px;")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)

        similarity = item['similarity']
        similarity_label = QLabel(f"Similarity: {similarity:.2f}%")

        if similarity >= 95:
            color = "#4CAF50"
        elif similarity >= 85:
            color = "#8BC34A"
        elif similarity >= 75:
            color = "#FFC107"
        else:
            color = "#FF9800"

        similarity_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        info_layout.addWidget(similarity_label)

        size_mb = item['size'] / (1024 * 1024)
        size_label = QLabel(f"Size: {size_mb:.2f} MB")
        size_label.setStyleSheet("color: #999999; font-size: 11px;")
        info_layout.addWidget(size_label)

        result_layout.addLayout(info_layout, stretch=1)

        btn_open = QPushButton("Open")
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_open.clicked.connect(lambda: self.open_file(item['path']))
        result_layout.addWidget(btn_open)
        
        self.results_layout.addWidget(result_widget)

    def open_file(self, file_path):
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Cannot open file:\n{e}')
    
    def closeEvent(self, event):
        if hasattr(self, 'cache_builder') and self.cache_builder.isRunning():
            self.cache_builder.stop()
            self.cache_builder.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))

    window = ImageFinder()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()