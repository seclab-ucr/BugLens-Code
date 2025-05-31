import unittest

# from helper.get_func_def import read_function_definition
from helper.get_func_def import read_func, read_line, read_func_first_part, read_func_second_part, read_line_with_previous_part
from common.config import PROJ_CONFIG
from read_result import parse_static_taint_analysis, get_insts_from_ctx, get_function, get_source_line_set


class TestGetFunc(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.proj_dir = PROJ_CONFIG["msm-sound"]["proj_dir"]

    def test_readline(self):
        file_path = "techpack/audio/dsp/q6adm.c"
        lineno = 3275
        function_source = read_line(file_path, lineno, self.proj_dir)
        print(function_source)

    def test_read_func(self):
        file_path = "sound/core/control.c"
        lineno = 1571
        function_source = read_func(file_path, lineno, self.proj_dir)
        self.assertTrue(function_source.startswith(
            "static long snd_ctl_ioctl("))
        print(function_source)

    def test_read_func2(self):
        file_path = "drivers/md/dm.c"
        lineno = 658
        function_source = read_func(file_path, lineno, self.proj_dir)
        self.assertTrue(function_source.startswith(
            "static struct table_device *find_table_device("))
        print(function_source)

    def test_read_func_first_part(self):
        filepath = "techpack/audio/dsp/q6adm.c"
        lineno = 3285
        function_source = read_func_first_part(filepath, lineno, self.proj_dir)
        print(function_source)

    def test_read_func_second_part(self):
        filepath = "sound/soc/codecs/adnc/iaxxx-codec.c"
        lineno = 5836
        function_source = read_func_second_part(
            filepath, lineno, self.proj_dir)
        print(function_source)

    def test_read_warn_list(self):
        warn_list_path = 'all_sound.cmd'
        bug_groups = parse_static_taint_analysis(warn_list_path)
        bug_groups = bug_groups[0:1]

        for group in bug_groups:
            print(f"Group ID: {group.group_id}")
            print('#'*80)
            warn = group.warns[0]
            last_order = warn.orders[-1]
            last_context = last_order.contexts_and_instructions[-1]

            source_line_set = {}
            last_line_in_file = {}
            for inst in last_context.instructions:
                # source_line_set.add({inst.file, inst.lineno})
                if inst.file not in source_line_set:
                    source_line_set[inst.file] = set()
                source_line_set[inst.file].add(inst.lineno)
                last_line_in_file[inst.file] = max(
                    inst.lineno, last_line_in_file.get(inst.file, 0))
            print('-'*80)

            for file, lineno in last_line_in_file.items():
                source_code_func = read_func_first_part(
                    file, lineno, self.proj_dir)
                # print(file, "line no:", lineno, end=': ')
                print(source_code_func)
                print('-'*80)

            for inst in last_context.instructions:
                print(inst)
            print('-'*80)

            for file in source_line_set:
                for lineno in source_line_set[file]:
                    source_code = read_line(file, lineno, self.proj_dir)
                    print(file.split('/')[-1], "Line :", lineno, end=': ')
                    print(source_code)
                    print('-'*80)

            # last_inst = last_context.instructions[-1]
            # file, lineno = last_inst.file, last_inst.lineno

            # print('='*80)
            # source_code = read_line(file, lineno, self.proj_dir)
            # print(source_code)
            # print('-'*80)
            # source_code_func = read_func(file, lineno, self.proj_dir)
            # print(source_code_func)

            print('#'*80)

    def test_read_warn_list2(self):
        warn_list_path = 'all_sound.cmd'
        bug_groups = parse_static_taint_analysis(warn_list_path)
        bug_group = bug_groups[0]

        context = bug_group.warns[0].orders[-1].contexts_and_instructions[-1]

        source_code = get_function(context, self.proj_dir)
        print(source_code)

        insts = get_insts_from_ctx(context, None)
        print(insts)

        source_line_set = get_source_line_set(context, self.proj_dir)
        print(source_line_set)

    def test_read_line(self):
        file_path = "sound/soc/msm/qdsp6v2/msm-lsm-client.c"
        lineno = 865
        dir = PROJ_CONFIG['codeql/ioctl-to-cfu']['proj_dir']
        # res = read_line(file_path, lineno, dir)
        res = read_line_with_previous_part(file_path, lineno, dir)
        print(res)

        ref = """
        		if (copy_from_user(prtd->lsm_client->sound_model.data,
			   snd_model_v2.data, snd_model_v2.data_size)) {
        """

        self.assertEqual(res.strip(), ref.strip())

    def test_read_line2(self):
        file_path = "sound/soc/msm/qdsp6v2/msm-lsm-client.c"
        dir = PROJ_CONFIG['codeql/ioctl-to-cfu']['proj_dir']

        lineno = 869
        res = read_line_with_previous_part(file_path, lineno, dir)
        print(res)

        ref = (
            '\t\t\tdev_err(rtd->dev,\n'
            '\t\t\t\t"%s: copy from user data failed\\n"\n'
            '\t\t\t       "data %pK size %d\\n", __func__,\n'
            '\t\t\t       snd_model_v2.data, snd_model_v2.data_size);'
        )
        self.assertEqual(res.strip(), ref.strip())

    def test_read_line3(self):
        file_path = "sound/soc/msm/qdsp6v2/msm-lsm-client.c"
        dir = PROJ_CONFIG['codeql/ioctl-to-cfu']['proj_dir']

        lineno = 897

        ref = (
            '\t\t\tdev_err(rtd->dev,\n'
            '\t\t\t\t"%s: Register snd Model v2 failed =%d\\n",\n'
            '\t\t\t       __func__, rc);'
        )

        res = read_line_with_previous_part(file_path, lineno, dir)
        print(res)
        self.assertEqual(res.strip(), ref.strip())
