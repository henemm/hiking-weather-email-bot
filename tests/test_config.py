import unittest
import os
import tempfile
import yaml
from wetter.config import validate_config, lade_konfiguration, ConfigValidationError, ConfigError

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit temporärer Konfigurationsdatei"""
        self.valid_config = {
            "startdatum": "2024-03-10",
            "smtp": {
                "host": "smtp.gmail.com",
                "port": 587,
                "user": "test@example.com",
                "to": "recipient@example.com"
            },
            "schwellen": {
                "regen": 50,
                "gewitter": 30,
                "wind": 40,
                "hitze": 35,
                "delta_prozent": 20
            }
        }
        
        # Erstelle temporäre Konfigurationsdatei
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        with open(self.config_path, 'w') as f:
            yaml.dump(self.valid_config, f)
    
    def tearDown(self):
        """Cleanup nach den Tests"""
        os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_validate_config_valid(self):
        """Test gültige Konfiguration"""
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
        
        # Test ohne schwellen
        invalid_config = self.valid_config.copy()
        del invalid_config['schwellen']
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
        
        # Test ungültiger Schwellenwert
        invalid_config = self.valid_config.copy()
        invalid_config['schwellen']['regen'] = -1
        with self.assertRaises(ConfigValidationError):
            validate_config(invalid_config)
    
    def test_lade_konfiguration_success(self):
        """Test erfolgreiches Laden der Konfiguration"""
        config = lade_konfiguration(self.config_path)
        self.assertEqual(config['startdatum'], '2024-03-10')
        self.assertEqual(config['smtp']['host'], 'smtp.gmail.com')
        self.assertEqual(config['smtp']['port'], 587)
        self.assertEqual(config['schwellen']['regen'], 50)
    
    def test_lade_konfiguration_file_not_found(self):
        """Test nicht existierende Konfigurationsdatei"""
        with self.assertRaises(ConfigError):
            lade_konfiguration('nicht_existierende_datei.yaml')
    
    def test_lade_konfiguration_invalid_yaml(self):
        """Test ungültiges YAML-Format"""
        with open(self.config_path, 'w') as f:
            f.write('invalid: yaml: content:')
        with self.assertRaises(ConfigError):
            lade_konfiguration(self.config_path)

if __name__ == '__main__':
    unittest.main() 