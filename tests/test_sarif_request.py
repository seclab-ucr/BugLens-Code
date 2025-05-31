import unittest
from unittest.mock import patch, MagicMock, call
from helper.dao import insert_log, create_connection
from common.config import DB_CONFIG
from parse_sarif import create_bug_groups_from_sarif
import prompts.call_api
import logging
from common.config import PROJ_CONFIG
from prompts.llm_analysis import infer_variable_name_llm
from read_result import Project

class TestSarif(unittest.TestCase):

    
    def test_infer_var(self):
        proj = PROJ_CONFIG['codeql/ioctl-to-cfu']
        self.proj = Project('codeql/ioctl-to-cfu', proj['sarif_file'], proj['proj_dir'])
        self.proj.bug_groups = create_bug_groups_from_sarif(proj['sarif_file'], proj['proj_dir'])
        with patch('prompts.call_api.do_request_llm') as mock_do_request_llm:
            def mock_behavior(model, temperature, max_tokens, formatted_messages, cur_prompt, round='N/A', case_id='N/A'):
                # logging.info(formatted_messages)
                print(formatted_messages)
                return "TEST_RESPONSE_IS_RESPONSE"
            
            mock_do_request_llm.side_effect = mock_behavior
            infer_variable_name_llm(self.proj, model='o3-mini', range_start=5, range_end=6, max_iters=1)
        # mocker.patch('prompts.call_api.do_request_llm', side_effect=mock_behavior)


