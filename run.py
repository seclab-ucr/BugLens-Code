import logging
from common.config import PROJ_CONFIG, MODEL_ABBR
from prompts.llm_analysis import infer_variable_name_llm, smart_bug_analysis_llm, sanitizer_detection_llm
from read_result import Project
from rich.logging import RichHandler
from parse_sarif import create_bug_groups_from_sarif
import os

import argparse

def run_per_proj(proj, args):
    if args.infer_var_name:
        infer_variable_name_llm(proj, model=args.model, range_start=args.range_start, range_end=args.range_end, max_iters=args.max_iters)
    if args.smart_bug_analysis:
        smart_bug_analysis_llm(proj, model=args.model, range_start=args.range_start, range_end=args.range_end, max_iters=args.max_iters)
    if args.sanitizer_detection:
        sanitizer_detection_llm(proj, model=args.model, range_start=args.range_start, range_end=args.range_end, max_iters=args.max_iters)
    


if __name__ == "__main__":
    FORMAT = "%(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

    parser = argparse.ArgumentParser(description='Run LLM analysis')
    parser.add_argument('--proj', type=str, help='Project name', default='msm-sound')
    parser.add_argument('--range_start', type=int, help='Start index of bug group', default=0)
    parser.add_argument('--range_end', type=int, help='End index of bug group', default=None)
    parser.add_argument('--single_case', type=int, help='Single case index', default=None)
    parser.add_argument('--max_iters', type=int, help='Max iterations for majority voting', default=1)    
    parser.add_argument('--model', type=str, help='Model name', default='o3-mini')

    parser.add_argument('--no-infer_var_name', action='store_false', help='Do not infer variable name', dest='infer_var_name', default=True)
    parser.add_argument('--no-smart_bug_analysis', action='store_false', help='Do not perform smart bug analysis', dest='smart_bug_analysis', default=True)
    parser.add_argument('--no-sanitizer_detection', action='store_false', help='Do not perform smart bug analysis', dest='sanitizer_detection', default=True)
    
    parser.add_argument('--project_name', type=str, help='Project name', default='msm-sound')
    
    args = parser.parse_args()
    
    if args.single_case is not None:
        args.range_start = args.single_case
        args.range_end = args.single_case + 1
        
    proj_name = args.proj
    if proj_name not in PROJ_CONFIG:
        logging.error(f"Project {proj_name} not found in the configuration, please add it to common/config.py")
        exit(1)
    logging.info(f"Running LLM analysis for project {proj_name}")
        
    if 'cmd_dir' in PROJ_CONFIG[proj_name]:
        proj_dir = PROJ_CONFIG[proj_name]['proj_dir']
        cmd_dir = PROJ_CONFIG[proj_name]['cmd_dir']
        projs = [Project(proj_name+"-"+cmd_file, os.path.join(cmd_dir, cmd_file),
                     proj_dir) for cmd_file in os.listdir(cmd_dir)]
    elif 'sarif_file' in PROJ_CONFIG[proj_name]:
        proj_dir = PROJ_CONFIG[proj_name]['proj_dir']
        sarif_file = PROJ_CONFIG[proj_name]['sarif_file']
        proj = Project(proj_name, sarif_file, proj_dir, no_groups=True)
        proj.bug_groups = create_bug_groups_from_sarif(sarif_file, proj_dir)
        projs = [proj]
    else:
        projs = [Project(proj_name, PROJ_CONFIG[proj_name]['cmd_file'], PROJ_CONFIG[proj_name]['proj_dir'])]


    if args.model in MODEL_ABBR:
        args.model = MODEL_ABBR[args.model]
    
    for proj in projs:
        run_per_proj(proj, args)