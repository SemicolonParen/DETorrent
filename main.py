import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.nexus_engine import NexusEngine
from gui.quantum_interface import QuantumInterface
from utils.system_validator import SystemValidator

class DetorrentLauncher:
    def __init__(self):
        self.application = QApplication(sys.argv)
        self.application.setApplicationName("Detorrent")
        self.application.setApplicationVersion("1.0.0")
        
    def initialize_system(self):
        validator = SystemValidator()
        if not validator.validate_privileges():
            print("Administrator privileges required")
            sys.exit(1)
        
        if not validator.validate_system_compatibility():
            print("System not compatible")
            sys.exit(1)
            
        return True
    
    def launch_interface(self):
        engine = NexusEngine()
        interface = QuantumInterface(engine)
        interface.show()
        return self.application.exec()

if __name__ == "__main__":
    launcher = DetorrentLauncher()
    if launcher.initialize_system():
        launcher.launch_interface()
