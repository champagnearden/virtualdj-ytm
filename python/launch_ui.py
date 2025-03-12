from typing import List
from song import Song
from index import search_songs, download_song, OUTPUT_PATH
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QWidget,
    QHeaderView,
    QScrollArea,
    QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from sys import argv, exit
from requests import get
from os import path

class DownloadThread(QThread):
    # Signal emitted when the download finishes
    finished = pyqtSignal()

    def __init__(self, song, path):
        super().__init__()
        self.song = song
        self.path = path

    def run(self):
        download_song(self.song, self.path)
        self.finished.emit()  # Emit the finished signal
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VirtualDj-YoutubeMusic")
        self.popup = None

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Path input
        path_layout = QHBoxLayout()
        self.path_field = QLineEdit()
        self.path_field.setText(OUTPUT_PATH)
        self.path_field.setPlaceholderText("Enter download directory...")
        self.path_field.setReadOnly(True)

        # Select Directory button
        self.select_button = QPushButton("Browse...")
        self.select_button.clicked.connect(self.select_directory)
        path_layout.addWidget(self.path_field)
        path_layout.addWidget(self.select_button)
        main_layout.addLayout(path_layout)

        # Search section
        search_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Enter your search query...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search_click)  # Connect button click to perform_search
        self.search_field.returnPressed.connect(self.on_search_click) # Connect enter press to perform_search
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Table section
        self.table = QTableWidget(0, 4)  # 4 columns: Title, Artist, Album, Duration
        self.table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Duration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self.display_details)  # Connect row click to details
        main_layout.addWidget(self.table)

        # Details section
        self.details_section = QScrollArea()
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_widget.setLayout(self.details_layout)
        self.details_section.setWidget(self.details_widget)
        self.details_section.setWidgetResizable(True)

        main_layout.addWidget(self.details_section)

    def perform_search(self, query: str):
        # Perform the search
        songs = search_songs(query)
        if len(songs) > 0:
            self.populate_table(songs)
        else:
            QMessageBox.critical(self, "Error", "No songs found")

    def populate_table(self, songs: List[Song]):
        self.songs = songs  # Save the song data for use in the details section
        self.table.setRowCount(0)  # Clear existing rows

        for song in songs:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(song.title))
            self.table.setItem(row_position, 1, QTableWidgetItem(song.artist))
            self.table.setItem(row_position, 2, QTableWidgetItem(song.album))
            self.table.setItem(row_position, 3, QTableWidgetItem(song.duration))

    def display_details(self, row, column):
        # Clear the details layout
        for i in reversed(range(self.details_layout.count())):
            widget = self.details_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Get the selected song
        song = self.songs[row]

        # Title
        title_label = QLabel(f"Title: {song.title}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.details_layout.addWidget(title_label)

        # Artist
        artist_label = QLabel(f"Artist: {song.artist}")
        self.details_layout.addWidget(artist_label)

        # Album
        album_label = QLabel(f"Album: {song.album}")
        self.details_layout.addWidget(album_label)

        # Duration
        duration_label = QLabel(f"Duration: {song.duration}")
        self.details_layout.addWidget(duration_label)

        # Thumbnail
        response = get(song.thumbnail_url[-1]['url'])
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        thumbnail_label = QLabel()
        thumbnail_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        self.details_layout.addWidget(thumbnail_label)

        # Download Button
        download_button = QPushButton("Download")
        download_button.clicked.connect(lambda: self.download_song(song))
        self.details_layout.addWidget(download_button)
    
    def close_popup(self, popup:QMessageBox, thread:QThread):
        popup.close()
        # Ensure the thread is cleaned up
        thread.quit()
        thread.wait()

    def download_song(self, song:Song):
        pixmap = QPixmap("./download.png")

        self.popup = QMessageBox()
        self.popup.setWindowTitle("Downloading...")
        self.popup.setText("Downloading...")
        if pixmap.isNull():
            print("Error: Unable to load image './download.png'")
        else:
            resized_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.popup.setIconPixmap(resized_pixmap)
        self.popup.setStandardButtons(QMessageBox.Ignore)
        self.popup.show()
        # Start the download in a separate QThread
        thread = DownloadThread(song, self.path_field.text())
        thread.finished.connect(lambda: self.close_popup(self.popup, thread))
        thread.start()

    def on_search_click(self):
        # Get the query from the search field
        query = self.search_field.text()
        if query:
            self.perform_search(query)
        else:
            QMessageBox.warning(self, "Warning", "Please enter a search query")

    def select_directory(self):
        # Open a dialog to select a directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            self.path_field.text()  # or some default path
        )
        # If a directory is selected, update the text field
        if directory:
            self.path_field.setText(directory)

if __name__ == "__main__":
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())
