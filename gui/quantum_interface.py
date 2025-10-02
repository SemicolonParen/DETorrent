import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QPushButton, QLineEdit, 
                             QTextEdit, QProgressBar, QComboBox, QListWidget, 
                             QListWidgetItem, QTabWidget, QGroupBox, QCheckBox,
                             QSpinBox, QSlider, QFileDialog, QMessageBox,
                             QSplitter, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from core.nexus_engine import NexusEngine

class QuantumInterface(QMainWindow):
    def __init__(self, engine: NexusEngine):
        super().__init__()
        self.engine = engine
        self.current_iso_path = None
        self.current_partition = None
        self.operation_thread = None
        
        self.init_ui()
        self.setup_connections()
        self.load_system_info()
        
    def init_ui(self):
        self.setWindowTitle("Detorrent - Quantum OS Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1000])
        
        self.apply_dark_theme()
        
    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        iso_group = QGroupBox("ISO Management")
        iso_layout = QVBoxLayout(iso_group)
        
        self.iso_path_edit = QLineEdit()
        self.iso_path_edit.setPlaceholderText("Select ISO file...")
        
        browse_btn = QPushButton("Browse ISO")
        browse_btn.clicked.connect(self.browse_iso)
        
        scan_btn = QPushButton("Scan Directory")
        scan_btn.clicked.connect(self.scan_directory)
        
        iso_layout.addWidget(QLabel("ISO File:"))
        iso_layout.addWidget(self.iso_path_edit)
        iso_layout.addWidget(browse_btn)
        iso_layout.addWidget(scan_btn)
        
        self.iso_list = QListWidget()
        iso_layout.addWidget(self.iso_list)
        
        layout.addWidget(iso_group)
        
        partition_group = QGroupBox("Partition Management")
        partition_layout = QVBoxLayout(partition_group)
        
        refresh_partitions_btn = QPushButton("Refresh Partitions")
        refresh_partitions_btn.clicked.connect(self.refresh_partitions)
        
        self.partition_list = QListWidget()
        
        partition_layout.addWidget(refresh_partitions_btn)
        partition_layout.addWidget(self.partition_list)
        
        layout.addWidget(partition_group)
        
        system_group = QGroupBox("System Information")
        system_layout = QVBoxLayout(system_group)
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setMaximumHeight(200)
        self.system_info_text.setReadOnly(True)
        
        system_layout.addWidget(self.system_info_text)
        
        layout.addWidget(system_group)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        tab_widget = QTabWidget()
        
        operation_tab = self.create_operation_tab()
        backup_tab = self.create_backup_tab()
        monitor_tab = self.create_monitor_tab()
        settings_tab = self.create_settings_tab()
        
        tab_widget.addTab(operation_tab, "OS Switch")
        tab_widget.addTab(backup_tab, "Backup")
        tab_widget.addTab(monitor_tab, "Monitor")
        tab_widget.addTab(settings_tab, "Settings")
        
        layout.addWidget(tab_widget)
        
        return panel
        
    def create_operation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        operation_group = QGroupBox("OS Switch Operation")
        operation_layout = QVBoxLayout(operation_group)
        
        self.preserve_data_checkbox = QCheckBox("Preserve existing data")
        self.preserve_data_checkbox.setChecked(True)
        
        self.auto_reboot_checkbox = QCheckBox("Auto-reboot after installation")
        self.auto_reboot_checkbox.setChecked(False)
        
        operation_layout.addWidget(self.preserve_data_checkbox)
        operation_layout.addWidget(self.auto_reboot_checkbox)
        
        self.execute_btn = QPushButton("Execute OS Switch")
        self.execute_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 10px; }")
        self.execute_btn.clicked.connect(self.execute_os_switch)
        
        operation_layout.addWidget(self.execute_btn)
        
        layout.addWidget(operation_group)
        
        progress_group = QGroupBox("Operation Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        log_group = QGroupBox("Operation Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(300)
        
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return tab
        
    def create_backup_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        backup_group = QGroupBox("Backup Operations")
        backup_layout = QVBoxLayout(backup_group)
        
        create_backup_btn = QPushButton("Create System Backup")
        create_backup_btn.clicked.connect(self.create_backup)
        
        restore_backup_btn = QPushButton("Restore from Backup")
        restore_backup_btn.clicked.connect(self.restore_backup)
        
        backup_layout.addWidget(create_backup_btn)
        backup_layout.addWidget(restore_backup_btn)
        
        layout.addWidget(backup_group)
        
        backup_list_group = QGroupBox("Available Backups")
        backup_list_layout = QVBoxLayout(backup_list_group)
        
        refresh_backups_btn = QPushButton("Refresh Backup List")
        refresh_backups_btn.clicked.connect(self.refresh_backups)
        
        self.backup_list = QListWidget()
        
        backup_list_layout.addWidget(refresh_backups_btn)
        backup_list_layout.addWidget(self.backup_list)
        
        layout.addWidget(backup_list_group)
        
        return tab
        
    def create_monitor_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        monitor_group = QGroupBox("System Monitoring")
        monitor_layout = QVBoxLayout(monitor_group)
        
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.memory_label = QLabel("Memory Usage: 0%")
        self.disk_label = QLabel("Disk Usage: 0%")
        
        monitor_layout.addWidget(self.cpu_label)
        monitor_layout.addWidget(self.memory_label)
        monitor_layout.addWidget(self.disk_label)
        
        start_monitor_btn = QPushButton("Start Monitoring")
        start_monitor_btn.clicked.connect(self.start_monitoring)
        
        stop_monitor_btn = QPushButton("Stop Monitoring")
        stop_monitor_btn.clicked.connect(self.stop_monitoring)
        
        monitor_layout.addWidget(start_monitor_btn)
        monitor_layout.addWidget(stop_monitor_btn)
        
        layout.addWidget(monitor_group)
        
        health_group = QGroupBox("System Health")
        health_layout = QVBoxLayout(health_group)
        
        self.health_text = QTextEdit()
        self.health_text.setReadOnly(True)
        self.health_text.setMaximumHeight(200)
        
        health_layout.addWidget(self.health_text)
        
        layout.addWidget(health_group)
        
        return tab
        
    def create_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        settings_group = QGroupBox("Application Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German"])
        
        settings_layout.addWidget(QLabel("Theme:"))
        settings_layout.addWidget(self.theme_combo)
        settings_layout.addWidget(QLabel("Language:"))
        settings_layout.addWidget(self.language_combo)
        
        layout.addWidget(settings_group)
        
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel("Detorrent v1.0.0\nQuantum OS Interface\nAdvanced OS Switching Technology")
        about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        
        return tab
        
    def setup_connections(self):
        self.iso_list.itemClicked.connect(self.on_iso_selected)
        self.partition_list.itemClicked.connect(self.on_partition_selected)
        
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitoring)
        
    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        
        self.setPalette(palette)
        
    def browse_iso(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("ISO Files (*.iso *.img *.dmg *.vdi *.vmdk)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.iso_path_edit.setText(selected_files[0])
                self.current_iso_path = selected_files[0]
                self.validate_iso()
                
    def scan_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.log_message(f"Scanning directory: {directory}")
            iso_files = self.engine.scan_available_isos(directory)
            
            self.iso_list.clear()
            for iso_file in iso_files:
                item = QListWidgetItem(iso_file['name'])
                item.setData(Qt.ItemDataRole.UserRole, iso_file['path'])
                self.iso_list.addItem(item)
                
    def validate_iso(self):
        if self.current_iso_path:
            self.log_message(f"Validating ISO: {self.current_iso_path}")
            validation_result = self.engine.validate_iso(self.current_iso_path)
            
            if validation_result['valid']:
                self.log_message("ISO validation successful")
            else:
                self.log_message(f"ISO validation failed: {validation_result['error']}")
                QMessageBox.warning(self, "Validation Error", f"ISO validation failed: {validation_result['error']}")
                
    def refresh_partitions(self):
        self.log_message("Refreshing partition list...")
        partitions = self.engine.partition_manager.list_partitions()
        
        self.partition_list.clear()
        for partition in partitions:
            if 'error' not in partition:
                if os.name == 'nt':
                    item_text = f"Partition {partition['number']} ({partition['letter']}) - {partition['size']} bytes"
                else:
                    item_text = f"{partition['name']} - {partition['size']} ({partition['fstype']})"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, partition)
                self.partition_list.addItem(item)
                
    def on_iso_selected(self, item):
        self.current_iso_path = item.data(Qt.ItemDataRole.UserRole)
        self.iso_path_edit.setText(self.current_iso_path)
        self.validate_iso()
        
    def on_partition_selected(self, item):
        self.current_partition = item.data(Qt.ItemDataRole.UserRole)
        
    def execute_os_switch(self):
        if not self.current_iso_path:
            QMessageBox.warning(self, "Error", "Please select an ISO file")
            return
            
        if not self.current_partition:
            QMessageBox.warning(self, "Error", "Please select a target partition")
            return
            
        reply = QMessageBox.question(self, "Confirm Operation", 
                                   "Are you sure you want to proceed with the OS switch? This operation cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_os_switch_operation()
            
    def start_os_switch_operation(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.execute_btn.setEnabled(False)
        
        preserve_data = self.preserve_data_checkbox.isChecked()
        
        if os.name == 'nt':
            target_partition = self.current_partition['letter']
        else:
            target_partition = self.current_partition['name']
        
        self.operation_thread = OsSwitchThread(self.engine, self.current_iso_path, target_partition, preserve_data)
        self.operation_thread.progress_updated.connect(self.update_progress)
        self.operation_thread.operation_completed.connect(self.operation_completed)
        self.operation_thread.start()
        
    def update_progress(self, progress, message):
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.log_message(message)
        
    def operation_completed(self, success, message):
        self.progress_bar.setVisible(False)
        self.execute_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("Operation completed successfully")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Operation failed")
            QMessageBox.critical(self, "Error", message)
            
    def create_backup(self):
        backup_path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if backup_path:
            self.log_message(f"Creating backup in: {backup_path}")
            result = self.engine.create_backup(backup_path)
            
            if result['success']:
                self.log_message("Backup created successfully")
                QMessageBox.information(self, "Success", "Backup created successfully")
            else:
                self.log_message(f"Backup failed: {result['error']}")
                QMessageBox.critical(self, "Error", f"Backup failed: {result['error']}")
                
    def restore_backup(self):
        backup_path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if backup_path:
            reply = QMessageBox.question(self, "Confirm Restore", 
                                       "Are you sure you want to restore from backup? This will overwrite current system data.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_message(f"Restoring from backup: {backup_path}")
                result = self.engine.restore_backup(backup_path)
                
                if result['success']:
                    self.log_message("Backup restored successfully")
                    QMessageBox.information(self, "Success", "Backup restored successfully")
                else:
                    self.log_message(f"Restore failed: {result['error']}")
                    QMessageBox.critical(self, "Error", f"Restore failed: {result['error']}")
                    
    def refresh_backups(self):
        backup_directory = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if backup_directory:
            backups = self.engine.backup_manager.list_backups(backup_directory)
            
            self.backup_list.clear()
            for backup in backups:
                if 'error' not in backup:
                    item_text = f"{backup['name']} - {backup['size']} bytes ({backup['created']})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, backup['path'])
                    self.backup_list.addItem(item)
                    
    def start_monitoring(self):
        self.monitor_timer.start(1000)
        self.log_message("System monitoring started")
        
    def stop_monitoring(self):
        self.monitor_timer.stop()
        self.log_message("System monitoring stopped")
        
    def update_monitoring(self):
        metrics = self.engine.system_monitor.get_current_metrics()
        
        if 'error' not in metrics:
            self.cpu_label.setText(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
            self.memory_label.setText(f"Memory Usage: {metrics['memory_percent']:.1f}%")
            
            health = self.engine.system_monitor.get_system_health()
            if 'error' not in health:
                health_text = f"Overall Status: {health['overall']}\n"
                if health['issues']:
                    health_text += "Issues:\n" + "\n".join(health['issues'])
                if health['recommendations']:
                    health_text += "\nRecommendations:\n" + "\n".join(health['recommendations'])
                
                self.health_text.setText(health_text)
                
    def change_theme(self, theme_name):
        if theme_name == "Dark":
            self.apply_dark_theme()
        elif theme_name == "Light":
            self.setStyleSheet("")
        self.log_message(f"Theme changed to: {theme_name}")
        
    def load_system_info(self):
        system_info = self.engine.get_system_info()
        
        if 'error' not in system_info:
            info_text = f"Platform: {system_info['platform']['system']}\n"
            info_text += f"Version: {system_info['platform']['version']}\n"
            info_text += f"Architecture: {system_info['platform']['architecture']}\n"
            info_text += f"Hostname: {system_info['platform']['hostname']}\n"
            
            self.system_info_text.setText(info_text)
            
    def log_message(self, message):
        timestamp = QTimer().remainingTime()
        self.log_text.append(f"[{timestamp}] {message}")

class OsSwitchThread(QThread):
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)
    
    def __init__(self, engine, iso_path, target_partition, preserve_data):
        super().__init__()
        self.engine = engine
        self.iso_path = iso_path
        self.target_partition = target_partition
        self.preserve_data = preserve_data
        
    def run(self):
        try:
            self.progress_updated.emit(10, "Preparing OS switch operation...")
            
            result = self.engine.execute_os_switch(self.iso_path, self.target_partition, self.preserve_data)
            
            if result['success']:
                self.progress_updated.emit(100, "OS switch completed successfully")
                self.operation_completed.emit(True, result['message'])
            else:
                self.operation_completed.emit(False, result['error'])
                
        except Exception as e:
            self.operation_completed.emit(False, str(e))
