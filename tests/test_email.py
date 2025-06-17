import unittest
from unittest.mock import patch, MagicMock
import smtplib
from email.mime.text import MIMEText
from emailversand import sende_email, EmailError

class TestEmail(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit Mock-Daten"""
        self.test_config = {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "user": "test@example.com",
                "password": "test123",
                "to": "recipient@example.com"
            }
        }
        self.test_report = "Test Wetterbericht\nTemperatur: 20°C\nRegen: 30%"

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test erfolgreicher E-Mail-Versand"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        result = sende_email(self.test_report, self.test_config)
        self.assertTrue(result)
        
        # Verify SMTP calls
        mock_smtp.assert_called_once_with(
            self.test_config["smtp"]["host"],
            self.test_config["smtp"]["port"]
        )
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with(
            self.test_config["smtp"]["user"],
            self.test_config["smtp"]["password"]
        )
        mock_smtp_instance.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_email_connection_error(self, mock_smtp):
        """Test Verbindungsfehler"""
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
        
        with self.assertRaises(EmailError):
            sende_email(self.test_report, self.test_config)

    @patch('smtplib.SMTP')
    def test_send_email_auth_error(self, mock_smtp):
        """Test Authentifizierungsfehler"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        
        with self.assertRaises(EmailError):
            sende_email(self.test_report, self.test_config)

    @patch('smtplib.SMTP')
    def test_send_email_invalid_config(self, mock_smtp):
        """Test ungültige Konfiguration"""
        invalid_config = {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587
                # Missing required fields
            }
        }
        
        with self.assertRaises(EmailError):
            sende_email(self.test_report, invalid_config)

    @patch('smtplib.SMTP')
    def test_send_email_retry_mechanism(self, mock_smtp):
        """Test Wiederholungsmechanismus"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # Simulate temporary failure then success
        mock_smtp_instance.send_message.side_effect = [
            smtplib.SMTPException("Temporary failure"),
            None
        ]
        
        result = sende_email(self.test_report, self.test_config)
        self.assertTrue(result)
        self.assertEqual(mock_smtp_instance.send_message.call_count, 2)

    def test_email_content_formatting(self):
        """Test E-Mail-Inhaltsformatierung"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
            
            sende_email(self.test_report, self.test_config)
            
            # Get the sent message
            sent_message = mock_smtp_instance.send_message.call_args[0][0]
            
            # Verify message format
            self.assertIsInstance(sent_message, MIMEText)
            self.assertEqual(sent_message['From'], self.test_config["smtp"]["user"])
            self.assertEqual(sent_message['To'], self.test_config["smtp"]["to"])
            self.assertIn("Wetterbericht", sent_message['Subject'])
            self.assertIn(self.test_report, sent_message.get_payload())

if __name__ == '__main__':
    unittest.main() 