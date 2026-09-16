"""
Virtual Pet Desktop Application - Main Entry Point
Run this file to start your virtual pet.
"""

import sys
import os

# Add project root to path so all imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from core.pet_window import PetWindow
from data.database   import Database


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Virtual Pet")
    app.setQuitOnLastWindowClosed(False)

    db = Database()
    db.initialize()

    pet = PetWindow(db)
    pet.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
