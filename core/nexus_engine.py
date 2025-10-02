import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .iso_manager import IsoManager
from .bootloader_manager import BootloaderManager
from .partition_manager import PartitionManager
from .os_detector import OsDetector
from .backup_manager import BackupManager
from .system_monitor import SystemMonitor

class NexusEngine:
    def __init__(self):
        self.iso_manager = IsoManager()
        self.bootloader_manager = BootloaderManager()
        self.partition_manager = PartitionManager()
        self.os_detector = OsDetector()
        self.backup_manager = BackupManager()
        self.system_monitor = SystemMonitor()
        self.current_operation = None
        self.operation_progress = 0
        
    def scan_available_isos(self, directory: str) -> List[Dict]:
        return self.iso_manager.scan_directory(directory)
    
    def validate_iso(self, iso_path: str) -> Dict:
        return self.iso_manager.validate_iso_file(iso_path)
    
    def detect_current_os(self) -> Dict:
        return self.os_detector.analyze_system()
    
    def prepare_target_os(self, iso_path: str) -> Dict:
        validation_result = self.validate_iso(iso_path)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['error']}
        
        os_info = self.os_detector.extract_os_info(iso_path)
        return {'success': True, 'os_info': os_info}
    
    def create_backup(self, backup_path: str) -> Dict:
        return self.backup_manager.create_system_backup(backup_path)
    
    def restore_backup(self, backup_path: str) -> Dict:
        return self.backup_manager.restore_system_backup(backup_path)
    
    def execute_os_switch(self, iso_path: str, target_partition: str, 
                         preserve_data: bool = True) -> Dict:
        try:
            self.current_operation = "os_switch"
            self.operation_progress = 0
            
            if preserve_data:
                backup_result = self.create_backup(tempfile.mkdtemp())
                if not backup_result['success']:
                    return {'success': False, 'error': 'Backup failed'}
            
            self.operation_progress = 20
            
            mount_result = self.iso_manager.mount_iso(iso_path)
            if not mount_result['success']:
                return {'success': False, 'error': 'ISO mount failed'}
            
            self.operation_progress = 40
            
            partition_result = self.partition_manager.prepare_partition(target_partition)
            if not partition_result['success']:
                return {'success': False, 'error': 'Partition preparation failed'}
            
            self.operation_progress = 60
            
            install_result = self.iso_manager.install_from_mounted(mount_result['mount_point'], 
                                                                 target_partition)
            if not install_result['success']:
                return {'success': False, 'error': 'Installation failed'}
            
            self.operation_progress = 80
            
            bootloader_result = self.bootloader_manager.configure_bootloader(target_partition)
            if not bootloader_result['success']:
                return {'success': False, 'error': 'Bootloader configuration failed'}
            
            self.operation_progress = 100
            
            return {'success': True, 'message': 'OS switch completed successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            self.current_operation = None
            self.operation_progress = 0
    
    def get_system_info(self) -> Dict:
        return self.system_monitor.get_comprehensive_info()
    
    def get_operation_status(self) -> Dict:
        return {
            'current_operation': self.current_operation,
            'progress': self.operation_progress
        }
