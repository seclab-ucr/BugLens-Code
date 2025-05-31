import json
import os
import re
from helper.get_func_def import get_func_start_line, read_func, read_line


class Instruction:
    def __init__(self, file, lineno, var_name, inst):
        self.file = file
        self.lineno = lineno
        self.var_name = var_name
        self.inst = inst

    def __repr__(self) -> str:
        return f"{self.file}:{self.lineno} {self.var_name} at {self.inst}"


def extract_var_name(line, start_column, end_column):
    """
    Extracts a variable name from a given line using the provided start and end columns.
    Columns are assumed to be 1-indexed. If end_column is valid, the substring from 
    start_column to end_column is used; otherwise, a heuristic is applied to expand left and right.
    """
    # Convert to 0-index.
    start_idx = start_column - 1 if start_column is not None else None
    end_idx = end_column - 1 if end_column is not None else None
    if start_idx is None or start_idx < 0 or start_idx >= len(line):
        return "unknown"
    if end_idx is not None and end_idx > start_idx and end_idx <= len(line):
        word = line[start_idx:end_idx]
        if word.strip():
            return word.strip()
    # Fallback: expand left and right to capture a word.
    left = start_idx
    right = start_idx
    while left > 0 and (line[left - 1].isalnum() or line[left - 1] == '_'):
        left -= 1
    while right < len(line) and (line[right].isalnum() or line[right] == '_'):
        right += 1
    word = line[left:right]
    return word if word else "unknown"


class FunctionCall:
    def __init__(self, file, start_line, column, function_definition, cur_inst, case_id):
        self.file = file
        self.start_line = start_line
        self.columns = [column] if column is not None else []
        self.instructions = [cur_inst]
        # Store full function definition for merging comparisons.
        self.full_function_definition = function_definition
        self.context = None
        self.case_id = case_id
        self.call_chain = ['not available, use "get_last_caller()" to get the last caller']
        self.desc = ""
        self.bug_group = None
        
        # For display, store only the first line.
        if function_definition:
            self.function_definition = function_definition.splitlines()[0]
        else:
            self.function_definition = None

    def merge(self, column, inst):
        if column is not None and column not in self.columns:
            self.columns.append(column)
            self.instructions.append(inst)

    def same_function(self, other_func_def):
        """
        Compare this function's definition with another by comparing the first 10 lines
        (or fewer if the function is shorter).
        """
        if not self.full_function_definition or not other_func_def:
            return False
        self_lines = self.full_function_definition.splitlines()
        other_lines = other_func_def.splitlines()
        n = min(10, len(self_lines), len(other_lines))
        for i in range(n):
            if self_lines[i].strip() != other_lines[i].strip():
                return False
        return True
    


class SARIFBugGroup:
    def __init__(self, group_id):
        self.group_id = int(group_id)
        self.func_list = []

    def get_last_context(self):
        return self.func_list[-1] if self.func_list else None
    
    def __repr__(self):
        return f"BugGroup {self.group_id}: {len(self.func_list)} function calls"


class SARIFContext:
    def __init__(self, proj_id, group_id):
        # call_chain stores FunctionCall objects.
        self.call_chain = ['not available, use "get_last_caller()" to get the last caller']
        # instructions stores Instruction objects.
        self.instructions = []
        self.case_id = f"{proj_id}:{group_id:04d}"
        # 'desc' is ignored as it is generated with a single rule.
        self.desc = ""

    def get_cur_func(self):
        if self.call_chain:
            return self.call_chain[-1].function_definition
        return None


def create_bug_groups_from_sarif(sarif_file_path, proj_path):
    """
    Parses a SARIF file and creates a list of SARIFBugGroup objects.

    Each result is converted into a bug group where:
      - The call_chain is built from dataflow steps. Dataflow steps are merged if they belong to the same
        function (either based on file path and function start line or if their function definitions match 
        for the first 10 lines).
      - The instructions are then filled by reading the line (via read_line) for each function call,
        and extracting the tainted variable (based on the column information).

    Args:
        sarif_file_path (str): Path to the SARIF file.
        proj_id (str or int): A project identifier.
        proj_path (str): Base directory of the source code.

    Returns:
        List[SARIFBugGroup]: A list of bug group objects.
    """
    bug_groups = []
    try:
        with open(sarif_file_path, 'r', encoding='utf-8') as f:
            sarif_data = json.load(f)
    except Exception as e:
        print(f"Error reading SARIF file: {e}")
        return bug_groups

    runs = sarif_data.get("runs", [])
    if not runs:
        print("No runs found in the SARIF file.")
        return bug_groups

    results = runs[0].get("results", [])
    if not results:
        print("No results found in this run.")
        return bug_groups

    for idx, result in enumerate(results):
        cur_bug = SARIFBugGroup(idx)
        # context = SARIFContext(proj_id, idx)
        code_flows = result.get("codeFlows", [])
        messages = result.get("message", {}).get("text", "")
        if messages:
            msg = messages.splitlines()[0]
        for flow in code_flows:
            for thread_flow in flow.get("threadFlows", []):
                for step in thread_flow.get("locations", []):
                    loc = step.get("location", {})
                    phys_loc = loc.get("physicalLocation", {})
                    artifact = phys_loc.get("artifactLocation", {})
                    file_path = artifact.get("uri", "Unknown file")
                    region = phys_loc.get("region", {})
                    step_line = region.get("startLine", None)
                    step_column = region.get("startColumn", None)
                    step_column_end = region.get("endColumn", None)

                    if file_path != "Unknown file" and step_line is not None:
                        try:
                            # Get the function's starting line and full definition.
                            func_start_line = get_func_start_line(
                                file_path, step_line, proj_path)
                            func_def = read_func(
                                file_path, step_line, proj_path)
                        except Exception as e:
                            func_start_line = step_line
                            func_def = None
                            print(
                                f"Error getting function info for {file_path} at line {step_line}: {e}")
                        
                        step_line_src = read_line(
                            file_path, step_line, proj_path)
                        cur_inst = Instruction(
                            file_path, step_line, extract_var_name(step_line_src, step_column, step_column_end), step_line_src.strip())

                        found = False
                        # Merge if same function: either same file & start_line, or matching function definitions.
                        for func_call in cur_bug.func_list:
                            if func_call.file == file_path and func_call.start_line == func_start_line:
                                func_call.merge(step_column, cur_inst)
                                found = True
                                break
                        if not found:
                            new_func_call = FunctionCall(
                                file_path, func_start_line, step_column, func_def, cur_inst, "{proj_id}:{idx:04d}")
                            # context.call_chain.append(new_func_call)
                            new_func_call.desc = msg
                            new_func_call.bug_group = cur_bug
                            cur_bug.func_list.append(new_func_call)
                            

        bug_groups.append(cur_bug)

    return bug_groups


if __name__ == "__main__":

    sarif_file_path = "results-overflow.sarif"
    proj_id = "codeql/ioctl-to-overflow"
    proj_path = "/home/lanran/codebase/for_suture/msm-4.4-revision-2017-May-07--08-33-56/src/home/kev/work/QualComm/semmle_data/projects/msm-4.4/revision-2017-May-07--08-33-56/kernel"

    bug_groups = create_bug_groups_from_sarif(
        sarif_file_path, proj_path)

    # Example output: iterate through the bug groups and print details.
    for group in bug_groups:
        print(f"Group ID: {group.group_id}")
        # for warn in group.warns:
        # for order in warn.orders:
        for context_and_inst in group.func_list:
            print("Function Calls: ", context_and_inst.call_chain)
            # for call in context_and_inst.function_calls:
            #     print(
            #         f"{call.function_name} at {call.source_link} called by {call.call_instruction}")
            print("Instructions:")
            for inst in context_and_inst.instructions:
                print(inst)
            print("\n")
        # _ = input("Press Enter to continue...")
        for __ in range(7):
            print("="*80)
