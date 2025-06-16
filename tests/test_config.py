import unittest
import os
import tempfile
import yaml
from wetter.config import (
    lade_konfiguration,
    validate_config,
    ConfigError,
    ConfigValidationError
)

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit temporärer Konfigurationsdatei"""
        self.valid_config = {
            'startdatum': '2024-06-15',
            'smtp': {
                'host': 'smtp.example.com',
                'port': 587,
                'user': 'test@example.com',
                'recipient': 'recipient@example.com',
                'subject': 'Wetterbericht'
            },
            'schwellenwerte': {
                'regen': 0.1,
                'gewitter': 0.1
            }
        }
        
        # Erstelle temporäre Konfigurationsdatei
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        with open(self.config_path, 'w') as f:
            yaml.dump(self.valid_config, f)

    def tearDown(self):
        """Aufräumen nach den Tests"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)

    def test_validate_config_valid(self):
        """Test gültige Konfiguration"""
        # Überprüfe, ob keine Exception geworfen wird
        validate_config(self.valid_config)

    def test_validate_config_missing_fields(self):
        """Test fehlende Pflichtfelder"""
        # Test ohne startdatum
        invalid_config = self.valid_config.copy()
        del invalid_config['startdatum']
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
        
        # Test ohne smtp
        invalid_config = self.valid_config.copy()
        del invalid_config['smtp']
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
        
        # Test ohne schwellenwerte
        invalid_config = self.valid_config.copy()
        del invalid_config['schwellenwerte']
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)

    def test_validate_config_invalid_types(self):
        """Test ungültige Datentypen"""
        # Test ungültiges startdatum
        invalid_config = self.valid_config.copy()
        invalid_config['startdatum'] = 123
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
        
        # Test ungültiger SMTP-Port
        invalid_config = self.valid_config.copy()
        invalid_config['smtp']['port'] = 'invalid'
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)

    def test_validate_config_invalid_values(self):
        """Test ungültige Werte"""
        # Test ungültiges Datum
        invalid_config = self.valid_config.copy()
        invalid_config['startdatum'] = 'invalid-date'
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
        
        # Test ungültiger SMTP-Port
        invalid_config = self.valid_config.copy()
        invalid_config['smtp']['port'] = 70000
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
        
        # Test negative Schwellenwerte
        invalid_config = self.valid_config.copy()
        invalid_config['schwellenwerte']['regen'] = -1
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)

    def test_lade_konfiguration_success(self):
        """Test erfolgreiches Laden der Konfiguration"""
        config = lade_konfiguration(self.config_path)
        self.assertEqual(config['startdatum'], '2024-06-15')
        self.assertEqual(config['smtp']['host'], 'smtp.example.com')
        self.assertEqual(config['smtp']['port'], 587)
        self.assertEqual(config['schwellenwerte']['regen'], 0.1)

    def test_lade_konfiguration_file_not_found(self):
        """Test nicht existierende Konfigurationsdatei"""
        with self.assertRaises(ConfigError):
            lade_konfiguration('nonexistent.yaml')

    def test_lade_konfiguration_invalid_yaml(self):
        """Test ungültiges YAML-Format"""
        # Schreibe ungültiges YAML
        with open(self.config_path, 'w') as f:
            f.write('invalid: yaml: content:')
        
        with self.assertRaises(ConfigError):
            lade_konfiguration(self.config_path)

if __name__ == '__main__':
    unittest.main() 