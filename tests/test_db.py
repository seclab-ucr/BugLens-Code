import unittest
from unittest.mock import patch, MagicMock, call
from helper.dao import insert_log, create_connection
from common.config import DB_CONFIG


class TestDB(unittest.TestCase):
    
    @patch('psycopg2.connect')
    def test_create_connection(self, mock_connect):
        create_connection()
        mock_connect.assert_called_once_with(**DB_CONFIG)
        
        