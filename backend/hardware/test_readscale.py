import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from itertools import cycle, chain

from readscale import get_weight


class TestGetWeight(unittest.TestCase):
    """Test cases for the get_weight function."""

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_success(self, mock_time, mock_sleep, mock_find):
        """Test successful weight reading with stable readings."""
        # Mock device setup
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        # Create mock endpoint structure: dev[0][(0, 0)][0]
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time to control the loop
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, then 7.0 (exits)
        # So we'll have ~11-12 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 7.0]
        
        # Mock USB read data: [status, status_with_stable_bit, 0, 0, grams_low, grams_high]
        # Status byte with bit 2 set (0x04) indicates stability
        # 500 grams = 0x01F4 = [0xF4, 0x01] -> data[4]=0xF4, data[5]=0x01
        # 510 grams = 0x01FE = [0xFE, 0x01] -> data[4]=0xFE, data[5]=0x01
        # 520 grams = 0x0208 = [0x08, 0x02] -> data[4]=0x08, data[5]=0x02
        
        stable_data_500 = [0x00, 0x04, 0x00, 0x00, 0xF4, 0x01]  # 500g, stable
        stable_data_510 = [0x00, 0x04, 0x00, 0x00, 0xFE, 0x01]  # 510g, stable
        stable_data_520 = [0x00, 0x04, 0x00, 0x00, 0x08, 0x02]  # 520g, stable
        
        # Provide enough readings to ensure last 3 are [510, 520, 520]
        # Then cycle the last value to avoid StopIteration
        reading_sequence = [stable_data_500] * 8 + [stable_data_510, stable_data_520, stable_data_520]
        mock_dev.read.side_effect = chain(reading_sequence, cycle([stable_data_520]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        # Should average last 3 readings: (510 + 520 + 520) / 3 = 516.67g = 0.517kg
        self.assertIn("total_weight_kg", result_dict)
        self.assertAlmostEqual(result_dict["total_weight_kg"], 0.517, places=2)
        
        # Verify device was configured and resources disposed
        mock_dev.set_configuration.assert_called_once()
        mock_find.assert_called_once_with(idVendor=0x0922, idProduct=0x8009)

    @patch('readscale.usb.core.find')
    def test_get_weight_scale_not_detected(self, mock_find):
        """Test error handling when scale is not detected."""
        mock_find.return_value = None
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "Scale not detected")

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_no_valid_readings(self, mock_time, mock_sleep, mock_find):
        """Test error handling when no stable readings are obtained."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time to control the loop
        mock_time.side_effect = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0]
        
        # All readings are unstable (status bit 2 not set)
        unstable_data = [0x00, 0x00, 0x00, 0x00, 0xF4, 0x01]  # 500g, unstable
        # Provide enough readings, then cycle to avoid StopIteration
        reading_sequence = [unstable_data] * 10
        mock_dev.read.side_effect = chain(reading_sequence, cycle([unstable_data]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "No valid readings")

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_usb_read_errors(self, mock_time, mock_sleep, mock_find):
        """Test handling of USB read errors during data collection."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time to control the loop
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, then 7.0 (exits)
        # So we'll have ~5-6 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 7.0]
        
        # Simulate USB errors followed by successful reads
        import usb.core
        stable_data = [0x00, 0x04, 0x00, 0x00, 0x64, 0x00]  # 100g, stable
        
        # Provide enough readings, then cycle to avoid StopIteration
        reading_sequence = [
            usb.core.USBError("USB read error"),
            usb.core.USBError("USB read error"),
            stable_data,  # Successful read after errors
            stable_data,
            stable_data,
        ] * 2
        mock_dev.read.side_effect = chain(reading_sequence, cycle([stable_data]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        # Should still get valid result despite initial errors
        self.assertIn("total_weight_kg", result_dict)
        self.assertEqual(result_dict["total_weight_kg"], 0.1)

    @patch('readscale.usb.core.find')
    @patch('readscale.usb.core.USBError')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_configuration_error_handled(self, mock_time, mock_sleep, mock_usb_error, mock_find):
        """Test that USB configuration errors are handled gracefully."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Simulate configuration error
        import usb.core
        mock_dev.set_configuration.side_effect = usb.core.USBError("Configuration error")
        
        # Mock time to control the loop
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, then 7.0 (exits)
        # So we'll have ~5-6 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 7.0]
        
        stable_data = [0x00, 0x04, 0x00, 0x00, 0xC8, 0x00]  # 200g, stable
        # Provide enough readings, then cycle to avoid StopIteration
        reading_sequence = [stable_data] * 6
        mock_dev.read.side_effect = chain(reading_sequence, cycle([stable_data]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        # Should still work despite configuration error
        self.assertIn("total_weight_kg", result_dict)
        self.assertEqual(result_dict["total_weight_kg"], 0.2)

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_short_data_packet(self, mock_time, mock_sleep, mock_find):
        """Test handling of data packets shorter than 6 bytes."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time to control the loop
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, then 7.0 (exits)
        # So we'll have ~5-6 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 7.0]
        
        # Short data packet (should be ignored)
        short_data = [0x00, 0x04, 0x00]  # Only 3 bytes
        stable_data = [0x00, 0x04, 0x00, 0x00, 0x96, 0x00]  # 150g, stable
        
        # Provide enough readings, then cycle to avoid StopIteration
        reading_sequence = [
            short_data,  # Should be ignored
            stable_data,  # Valid reading
            stable_data,
            stable_data,
        ] * 2
        mock_dev.read.side_effect = chain(reading_sequence, cycle([stable_data]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        # Should still get valid result (short packets ignored)
        self.assertIn("total_weight_kg", result_dict)
        self.assertEqual(result_dict["total_weight_kg"], 0.15)

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_averages_last_three(self, mock_time, mock_sleep, mock_find):
        """Test that only the last 3 stable readings are averaged."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time to control the loop
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, then 7.0 (exits)
        # So we'll have ~11-12 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 7.0]
        
        # Multiple readings: only last 3 should be averaged
        # 100g, 200g, 300g, 400g, 500g
        # We want last 3 to be [300, 400, 500] = 0.4kg
        reading_100 = [0x00, 0x04, 0x00, 0x00, 0x64, 0x00]  # 100g
        reading_200 = [0x00, 0x04, 0x00, 0x00, 0xC8, 0x00]  # 200g
        reading_300 = [0x00, 0x04, 0x00, 0x00, 0x2C, 0x01]  # 300g
        reading_400 = [0x00, 0x04, 0x00, 0x00, 0x90, 0x01]  # 400g
        reading_500 = [0x00, 0x04, 0x00, 0x00, 0xF4, 0x01]  # 500g
        
        # Provide enough readings to ensure last 3 are [300, 400, 500]
        # Then cycle the last value to avoid StopIteration
        reading_sequence = [reading_100, reading_200] + [reading_300, reading_400, reading_500] * 3
        mock_dev.read.side_effect = chain(reading_sequence, cycle([reading_500]))
        
        result = get_weight(wait_time=6.0)
        result_dict = json.loads(result)
        
        # Should average last 3: (300 + 400 + 500) / 3 = 400g = 0.4kg
        self.assertIn("total_weight_kg", result_dict)
        self.assertAlmostEqual(result_dict["total_weight_kg"], 0.4, places=3)

    @patch('readscale.usb.core.find')
    @patch('readscale.time.sleep')
    @patch('readscale.time.time')
    def test_get_weight_custom_wait_time(self, mock_time, mock_sleep, mock_find):
        """Test that custom wait_time parameter is respected."""
        mock_dev = MagicMock()
        mock_endpoint = Mock()
        mock_endpoint.bEndpointAddress = 0x81
        mock_endpoint.wMaxPacketSize = 8
        
        mock_interface = MagicMock()
        mock_interface.__getitem__ = Mock(return_value=mock_endpoint)
        mock_config = MagicMock()
        mock_config.__getitem__ = Mock(return_value=mock_interface)
        mock_dev.__getitem__ = Mock(return_value=mock_config)
        
        mock_find.return_value = mock_dev
        
        # Mock time with shorter wait time (3 seconds)
        # start_time = 0.0, then loop checks at: 0.5, 1.0, 1.5, 2.0, 2.5, then 4.0 (exits)
        # So we'll have ~5-6 readings before exit
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 4.0]
        
        stable_data = [0x00, 0x04, 0x00, 0x00, 0x32, 0x00]  # 50g, stable
        # Provide enough readings, then cycle to avoid StopIteration
        reading_sequence = [stable_data] * 6
        mock_dev.read.side_effect = chain(reading_sequence, cycle([stable_data]))
        
        result = get_weight(wait_time=3.0)
        result_dict = json.loads(result)
        
        # Should complete successfully with shorter wait time
        self.assertIn("total_weight_kg", result_dict)
        self.assertEqual(result_dict["total_weight_kg"], 0.05)


if __name__ == '__main__':
    unittest.main()

