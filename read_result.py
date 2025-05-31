import re

from helper.get_func_def import read_func_first_part, read_func_second_part, read_line, read_func
import argparse

class Project:
    def __init__(self, proj_id, path, proj_dir, no_groups=False):
        self.proj_id = proj_id
        self.path = path
        if no_groups:
            self.bug_groups = None
        else:
            self.bug_groups = parse_static_taint_analysis(path, proj_id)
        self.proj_dir = proj_dir


class FunctionCall:
    def __init__(self, function_name, source_link, call_instruction=None):
        self.function_name = function_name
        self.source_link = source_link
        self.call_instruction = call_instruction


_file_path_prefix = ["private/msm-google/"]


def remove_prefix(text):
    for prefix in _file_path_prefix:
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


class Inst:
    def __init__(self, source, inst=None):
        self.source = source = remove_prefix(source)
        self.file, self.lineno = source.split("@")
        self.lineno = int(self.lineno)
        self.inst = inst

    def __repr__(self) -> str:
        return f"{self.file}:{self.lineno} at {self.inst}"


class ContextAndInstructions:
    def __init__(self, proj_id, group_id, desc):
        self.call_chain = []
        self.function_calls = []
        self.instructions = []
        self.case_id = f"{proj_id}:{group_id:04d}"
        self.desc = desc.split("says:")[0].strip()

    def get_cur_func(self):
        return self.function_calls[-1].function_name


class Order:
    def __init__(self):
        self.contexts_and_instructions = []


class Warn:
    def __init__(self):
        self.orders = []
        self.desc = ""


class BugGroup:
    def __init__(self, group_id):
        self.group_id = int(group_id)
        self.warns = []

    def get_last_context(self):
        warn = self.warns[0]
        last_order = warn.orders[-1]
        last_context = last_order.contexts_and_instructions[-1]
        return last_context


def parse_static_taint_analysis(file_path, proj_id="N/A"):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    bug_groups = []
    current_group = None
    current_warn = None
    current_order = None
    current_context = None
    in_context = False
    in_insts = False
    ignore_cur_trace = False
    new_order = True

    for line in lines:
        if "=========================" in line:
            group_id = re.search(r'GROUP (\d+)', line).group(1)
            current_group = BugGroup(group_id)
            bug_groups.append(current_group)
            in_context = False
            in_insts = False
            new_order = True
        elif "++++++++++++++++WARN 0" in line and current_group is not None:
            current_warn = Warn()
            current_group.warns.append(current_warn)
            ignore_cur_trace = False
        elif ignore_cur_trace:
            continue
        elif "********Trace 0" in line:
            continue
        elif "********Trace 1" in line:
            ignore_cur_trace = True
            continue
        elif "++++++++++++++++WARN 1" in line:
            ignore_cur_trace = True
            continue
        elif 'says:' in line:
            current_warn.desc = line.strip()
        elif "#####CTX#####" in line:
            if new_order:
                current_order = Order()
                current_warn.orders.append(current_order)
                new_order = False

            current_context = ContextAndInstructions(
                group_id=current_group.group_id, proj_id=proj_id, desc=current_warn.desc)
            current_order.contexts_and_instructions.append(current_context)

            current_context.call_chain = line[14:].strip().split(" -> ")
            in_context = True
            in_insts = False
        elif "#####INSTS#####" in line:
            in_context = False
            in_insts = True
        elif ">>>>>>>>>>>>" in line:
            # Start of a new order within the same warn
            new_order = True
            continue  # Skip this line to not add separator as instruction
        elif in_context:
            # two cases: function loc, and calling instruction
            if line.startswith("---->"):  # calling instruction
                call_instruction = line[6:]
                source, call_instruction = call_instruction.split(" :   ")
                current_context.function_calls[-1].call_instruction = Inst(
                    source, call_instruction)
            else:  # function loc
                function_name, source = line.split(" (")
                source = source.rstrip(")")
                current_context.function_calls.append(
                    FunctionCall(function_name, source.strip()))

        elif in_insts and line.strip():
            # current_context.instructions.append(line.strip())
            dem_index = line.find(" (")
            source = line[:dem_index]
            inst = line[dem_index+2:].strip()

            # source, inst = line.strip().split(" (")
            inst = inst.rstrip(")")
            current_context.instructions.append(Inst(source, inst.strip()))

    return bug_groups

# @DeprecationWarning
# def get_last_context(bug_group:BugGroup):
#     warn = bug_group.warns[0]
#     last_order = warn.orders[-1]
#     last_context = last_order.contexts_and_instructions[-1]
#     return last_context


def flatten_data(bug_groups):
    # Prepare a list to hold all flattened entries
    data = []

    for group in bug_groups:
        for warn_index, warn in enumerate(group.warns):
            for order_index, order in enumerate(warn.orders):
                for context_and_instructions in order.contexts_and_instructions:
                    for function_call in context_and_instructions.function_calls:
                        for instruction in context_and_instructions.instructions:
                            # Flatten and structure the row
                            row = {
                                'Group ID': group.group_id,
                                'Warn Index': warn_index,
                                'Order Index': order_index,
                                'Function Name': function_call.function_name,
                                'Source Link': function_call.source_link,
                                'Call Instruction': function_call.call_instruction,
                                'Instruction Source': instruction.source if isinstance(instruction, Inst) else None,
                                'Instruction Detail': instruction.inst if isinstance(instruction, Inst) else instruction
                            }
                            data.append(row)

    return data


"""
get_insts_lineno_set: get the set of inst_line_no
"""


# def get_insts_lineno_set(insts):
#     source_line_set = {}
#     last_line_in_file = {}

#     for inst in insts:
#         if inst.file not in source_line_set:
#             source_line_set[inst.file] = set()
#         source_line_set[inst.file].add(inst.lineno)
#         last_line_in_file[inst.file] = max(
#             inst.lineno, last_line_in_file.get(inst.file, 0))

#     return source_line_set, last_line_in_file


def get_function(context, proj_dir):
    return _get_function_parts(context, proj_dir, read_func)


def get_function_first_part(context, proj_dir):
    return _get_function_parts(context, proj_dir, read_func_first_part)


def get_function_second_part(context, proj_dir):
    return _get_function_parts(context, proj_dir, read_func_second_part)


def _get_function_parts(context, proj_dir, read_func_part):
    res = ""
    last_line_in_file = {}
    for inst in context.instructions:
        last_line_in_file[inst.file] = max(
            inst.lineno, last_line_in_file.get(inst.file, 0))

    for file, lineno in last_line_in_file.items():
        res += "File: " + file + "\n"
        res += "```c\n"

        source_code_func = read_func_part(file, lineno, proj_dir)
        res += source_code_func
        res += "```\n"

    return res


def get_insts_from_ctx(context):
    res = "```LLVM\n"
    for inst in context.instructions:
        res += str(inst) + "\n"
    res += "```\n"
    return res


def get_source_line_set(context, proj_dir):
    res = ""
    source_line_set = {}
    for inst in context.instructions:
        if inst.file not in source_line_set:
            source_line_set[inst.file] = set()
        source_line_set[inst.file].add(inst.lineno)

    for file in source_line_set:
        for lineno in source_line_set[file]:
            source_code = read_line(file, lineno, proj_dir)
            res += file.split('/')[-1] + " Line :" + str(lineno) + ": "
            res += source_code + "\n"

    return res


# def get_case_info(group_id, bug_groups):
#     group = bug_groups[group_id]
#     warn = group.warns[0]
#     last_order = warn.orders[-1]
#     last_context = last_order.contexts_and_instructions[-1]

if __name__ == "__main__":
    # Usage example:
    # file_path = 'example_sound.cmd'
    parser = argparse.ArgumentParser(description='Read result file')
    parser.add_argument('--file_path', type=str, help='Path to the result file', default='all_sound.cmd')
    
    args = parser.parse_args()
    file_path = args.file_path
    bug_groups = parse_static_taint_analysis(file_path)
    # p = Project("msm-android-10", "all_sound.cmd")

    for group in bug_groups:
        # for i, group in enumerate(bug_groups):
        print(f"Group ID: {group.group_id}")
        # for warn in group.warns:
        warn = group.warns[0]
        # for order in warn.orders:
        for order_id, order in enumerate(warn.orders):
            print(f"order: {order_id}")
            for context_and_inst in order.contexts_and_instructions:
                print("Function Calls: ", context_and_inst.call_chain)
                # for call in context_and_inst.function_calls:
                #     print(
                #         f"{call.function_name} at {call.source_link} called by {call.call_instruction}")
                print("Instructions:")
                for inst in context_and_inst.instructions:
                    print(inst)
                print("\n")
        print(f"Description: {warn.desc}")
        # _ = input("Press Enter to continue...")
        for __ in range(7):
            print("="*80)
