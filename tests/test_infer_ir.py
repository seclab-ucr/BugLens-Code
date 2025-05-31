from helper.infer_ir import parse_ir_file, extract_function, perform_taint_analysis, parse_instruction_line
import unittest


class TestInferIR(unittest.TestCase):
    
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.ir_file = 'sound-O0.ll'
        # self.module = parse_ir_file(self.ir_file)
        
    
    def test_parse_inst(self):
        insts = 'sound/core/pcm_lib.c:1736 at %18 = load i32, i32* %channel9, align 8, !dbg !637632'
        res = parse_instruction_line(insts)
        print(res)
        
    # def get_real_dbg(self):
        func_name = 'adm_open'
        module = parse_ir_file(self.ir_file)
        # extracted_func = extract_function(self.module, func_name)
        print(len(module.functions))