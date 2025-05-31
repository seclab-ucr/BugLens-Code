import unittest
from unittest.mock import patch
import prompts.call_api
import helper.dao as dao
from common.config import PROJ_CONFIG
import logging, sys

from read_result import parse_static_taint_analysis
from prompts.llm_analysis import PROMPT
from prompts.call_api import get_request_list, get_from_response

logger = logging.getLogger()

class TestGPT(unittest.TestCase):
    
    def setUp(self):
        # self.proj_dir = PROJ_DIR["msm-android-10"]
        self.proj_dir = PROJ_CONFIG["msm-sound"]["proj_dir"]
        warn_list_path = 'all_sound.cmd'
        bug_groups = parse_static_taint_analysis(warn_list_path)
        bug_group = bug_groups[0]
        self.context = bug_group.get_last_context()
        self.task = {"id": "N/A", "proj_dir": self.proj_dir, "context": self.context, "case_id": "test_id"}
        self.prompts = PROMPT['smart_bug_analysis']
        
    
    @patch('prompts.call_api.do_request_llm')
    def test_prompt(self, mock_do_request_llm):
        mock_do_request_llm.side_effect = lambda *args: "TEST_RESPONSE_IS_RESPONSE"
        _ = 0
        res = prompts.call_api.do_request_series("model", 0, 0, self.prompts , self.task)
        
        print(res)
        
        
    def test_callback_requests(self):
        response = """
        my request is as follows:
        ```
            <requests>
              <request>
                <name>need_func_def</name>
                <args>
                  <arg>func_1</arg>
                  <arg>func_2</arg>
                </args>
              </request>
              <request>
                <name>need_struct_def</name>
                <args>
                  <arg>struct_name_1</arg>
                  <arg>struct_name_2</arg>
                </args>
              </request>
            </requests>
        ```
        """
        request_body = get_from_response(response, 'requests')
        request_list = get_request_list(request_body)
        print(request_list)
        
    def test_callback_requests2(self):
        response = """
        Response: <requests>                                                            
                      <request>                                                                     
                        <name>need_global_var_def</name>                                            
                        <args>                                                                      
                          <arg>this_adm</arg>                                                       
                        </args>                                                                     
                      </request>                                                                    
                    </requests>  
        """
        request_body = get_from_response(response, 'requests')
        
        # unittest.TestCase().assertEqual(1, 1)
        
    def test_callback_requests3(self):
        response = """
        about its definition and how `max` is computed. Please provide:                                                              
                                                                                                                                                 
                    <requests>                                                                                                                   
                    1. Definition of the struct containing `msm_srs_trumedia_params.raw_params` (e.g., `struct                                   
                    msm_srs_trumedia_params`).                                                                                                   
                    2. The code or logic defining the value of `max` in the function (e.g., how `max` is derived or initialized).                
                    </requests>                                                                                                                  
                                                                                                                                                 
                    Without this information, here’s the preliminary analysis:  
        """
        request_body = get_from_response(response, 'requests')
        print(request_body)
        reqest_list = get_request_list(request_body)
        print(reqest_list)
        