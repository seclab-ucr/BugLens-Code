import unittest
import logging

import helper.codequery
from helper.callbacks import function_retrieve_callback, global_var_retrieve_callback, struct_retrieve_callback
from helper.codequery import get_struct_def_codequery
from helper.get_func_def import read_struct_def

class TestFindFuncCQ(unittest.TestCase):
    def test(self):
        logging.basicConfig(level=logging.DEBUG)
        helper.codequery.create_cq_db("/home/lanran/codebase/for_suture/msm-android-10")
        
    def test_find_func_cq(self):
        logging.basicConfig(level=logging.DEBUG)
        res = helper.codequery.get_func_def_codequery("/home/lanran/codebase/for_suture/msm-android-10", "slim_tx_ch_put")
        logging.info(res)
        
        response = """
        <args>
        <arg>slim_tx_ch_put</arg>
        </args>
        """
        res = function_retrieve_callback.call({"proj_dir": "/home/lanran/codebase/for_suture/msm-android-10"}, response)
        print(res)
        
    def test_find_roundup(self):
        logging.basicConfig(level=logging.DEBUG)
        # res = helper.find_func_cq.get_func_def_codequery("/home/lanran/codebase/for_suture/msm-android-10", "slim_tx_ch_put")
        # logging.info(res)
        
        response = """
        <args>
        <arg>roundup</arg>
        </args>
        """
        res = function_retrieve_callback.call({"proj_dir": "/home/lanran/codebase/for_suture/msm-android-10"}, response)
        print(res)
        
    def test_find_func_cq2(self):
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
        res = get_struct_def_codequery(proj_path, "audproc_volume_ctrl_master_gain")
        print(res)
        file, lineno = res[0]
        
        code = read_struct_def(file, int(lineno), proj_path)
        print(code)
        
    def test_find_global_var(self):
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
        res = helper.codequery.get_global_var_def_codequery(proj_path, "slim_rx_cfg")
        print(res)
        
    def test_find_global_var2(self):
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
        # res = helper.codequery.get_global_var_def_codequery(proj_path, "MAX_CHANNELS")
        # print(res)
        args = ['MAX_CHANNELS', 'SND_US16X08_KCMIN']
        
        res1 = function_retrieve_callback.call({"proj_dir": proj_path}, args)
        print(res1)
        self.assertTrue("#define MAX_CHANNELS" in res1)
        
        res2 = global_var_retrieve_callback.call({"proj_dir": proj_path}, args)
        print(res2)
        
        # self.assertEqual(res1.strip(), res2.strip())
        self.assertTrue("#define MAX_CHANNELS" in res2)
        self.assertTrue("#define SND_US16X08_KCMIN" in res2)
        
    def test_find_global_var3(self):
        # enum variables
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
    
        res = global_var_retrieve_callback.call({"proj_dir": proj_path}, ['IAXXX_ACLK_FREQ_NONE', 'IAXXX_ACLK_FREQ_3072'])
        print(res)
        # res = struct_retrieve_callback.call({"proj_dir": proj_path}, ['IAXXX_ACLK_FREQ_NONE', 'IAXXX_ACLK_FREQ_3072'])
        # print(res)
        
        
    def test_find_marco3(self):
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
        res = global_var_retrieve_callback.call({"proj_dir": proj_path}, ['EQ_CONFIG_PARAM_LEN'])
        print(res)
    
        
    def test_find_union(self):
        logging.basicConfig(level=logging.DEBUG)
        proj_path = "/home/lanran/codebase/for_suture/msm-android-10"
        union_name = 'afe_port_config'
        # res = helper.codequery.get_struct_def_codequery(proj_path, union_name)
        res = struct_retrieve_callback.call({"proj_dir": proj_path}, [union_name])
        print(res)