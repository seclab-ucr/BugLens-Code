from prompts.call_api import do_request_series, get_from_response
from helper.dao import * 
import yaml
import re

import logging
from rich.progress import track


def _read_prompt_file():
    prompt_file = "prompts/request.yaml"
    with open(prompt_file, "r") as f:
        prompts = yaml.safe_load(f)
    return prompts



PROMPT = _read_prompt_file()


def run_with_majority_voting(context, prompts, task, model, temperature, max_tokens, xml_tag, case_id, max_iters):
    res_count = {}
    # optimize: if any result appears more than half of the time, we can directly return it
    # if answered with "uncertain", we drop this iteration (but at most one more iteration)
    one_more_iter = True
    failed_before = False
    abs_majority = max_iters // 2 + 1
    
    # if the task has nothing, skip
    if not task or not task['context']:
        logging.error(f"Task {task['id']} has no context")
        return None
    
    for _ in range(max_iters):
        msg = do_request_series(model, temperature, max_tokens, prompts, task)
        if msg is None:
            if failed_before:
                return None
            failed_before = True
            continue
        
        response = msg[-1]['content']
        res = get_from_response(response, xml_tag)
        if res:
            if res in res_count:
                res_count[res] += 1
            else:
                res_count[res] = 1
        else:
            continue
        
        
        if res == "uncertain" and one_more_iter:
            max_iters += 1
            one_more_iter = False
        
        if res_count and max(res_count.values()) >= abs_majority:
            break
        
    # find the most common result
    return max(res_count, key=res_count.get) if res_count else None


def infer_variable_name_llm(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    prompts = PROMPT['infer_variable_name']
    bug_groups = proj.bug_groups

    if range_end is None:
        range_end = len(bug_groups)
    bug_groups = bug_groups[range_start:range_end]

    # for bug_group in bug_groups:
    for bug_group in track(bug_groups, description="Infer variable name"):
        context = bug_group.get_last_context()
        task = {"id": "var_name", "proj_dir": proj.proj_dir, "context": context,
                "case_id": f"{proj.proj_id}:{bug_group.group_id:04d}"}
        # msg = do_request_series(model, temperature, max_tokens, prompts, task)
        # response = msg[-1]['content']

        # var_name = _get_var_from_response(response)
        res = run_with_majority_voting(
            context, prompts, task, model, temperature, max_tokens, 'infer_res', task['case_id'], max_iters)
        
        if res:
            insert_or_update_varname(task['case_id'], res, model)
        else:
            logging.error(
                f"Failed to infer variable name for {task['case_id']}")


def smart_bug_analysis_llm(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    prompts = PROMPT['smart_bug_analysis']
    bug_groups = proj.bug_groups

    # bug_groups = bug_groups[6:10]
    if range_end is None:
        range_end = len(bug_groups)
    bug_groups = bug_groups[range_start:range_end]

    # for bug_group in bug_groups:
    for bug_group in track(bug_groups, description="Smart bug analysis"):
        context = bug_group.get_last_context()
        task = {"id": "smart_bug_analysis", "proj_dir": proj.proj_dir,
                "context": context, "case_id": f"{proj.proj_id}:{bug_group.group_id:04d}"}
        res = run_with_majority_voting(
            context, prompts, task, model, temperature, max_tokens, 'bug_eval', task['case_id'], max_iters)
        if res:
            insert_or_update_analysis(task['case_id'], res, model)
        else:
            logging.error(
                f"Failed to infer analysis for {task['case_id']}")
            
def __is_false_alarm_by_analysis(case_id, model):
    # t = find_analysis_result(case_id, model)[0]
    ana_res = find_analysis_result(case_id, model)
    if ana_res is None:
        return True
    t = ana_res[0]
    if t is None:
        return True
    # return not "<bug_eval>potential_bug</bug_eval>" in t
    return 'not_a_bug' in t
    
def sanitizer_detection_llm(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    # sanitizer_detection_p1(proj, model, temperature, max_tokens, range_start, range_end, max_iters)
    # sanitizer_detection_p2(proj, model, temperature, max_tokens, range_start, range_end, max_iters)
    sanitizer_detection(proj, model, temperature, max_tokens, range_start, range_end, max_iters)
    
    
def sanitizer_detection(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    prompts = PROMPT['sanitizer_detection']
    bug_groups = proj.bug_groups

    # bug_groups = bug_groups[6:10]
    if range_end is None:
        range_end = len(bug_groups)
    bug_groups = bug_groups[range_start:range_end]

    # for bug_group in bug_groups:
    for bug_group in track(bug_groups, description="Sanitizer detection"):
        # filter: if "smart bug analysis" is not a bug
        if __is_false_alarm_by_analysis(f"{proj.proj_id}:{bug_group.group_id:04d}", model):
            insert_or_update_sanitizer(f"{proj.proj_id}:{bug_group.group_id:04d}", "not_a_bug", model)
            continue
        
        context = bug_group.get_last_context()
        task = {"id": "sanitizer_detection_p1", "proj_dir": proj.proj_dir,
                "context": context, "case_id": f"{proj.proj_id}:{bug_group.group_id:04d}"}
        res = run_with_majority_voting(
            context, prompts, task, model, temperature, max_tokens, 'final_res', task['case_id'], max_iters)
        if res:
            insert_or_update_sanitizer(task['case_id'], res, model)
        else:
            insert_or_update_sanitizer(task['case_id'], "error", model)
            logging.error(
                f"Failed to infer analysis for {task['case_id']}")

def sanitizer_detection_p1(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    prompts = PROMPT['sanitizer_detection_p1']
    bug_groups = proj.bug_groups

    # bug_groups = bug_groups[6:10]
    if range_end is None:
        range_end = len(bug_groups)
    bug_groups = bug_groups[range_start:range_end]

    # for bug_group in bug_groups:
    for bug_group in track(bug_groups, description="Sanitizer detection"):
        # filter: if "smart bug analysis" is not "bug", the skip:
        if __is_false_alarm_by_analysis(f"{proj.proj_id}:{bug_group.group_id:04d}", model):
            continue
        
        context = bug_group.get_last_context()
        task = {"id": "sanitizer_detection_p1", "proj_dir": proj.proj_dir,
                "context": context, "case_id": f"{proj.proj_id}:{bug_group.group_id:04d}"}
        res = run_with_majority_voting(
            context, prompts, task, model, temperature, max_tokens, 'res', task['case_id'], max_iters)
        if res:
            # insert_or_update_sanitizer(task['case_id'], res, model)
            # insert_or_update_req_sanitizer(task['case_id'], res, model)
            # UPDATE: consider change the order
            insert_or_update_detected_sanitizer(task['case_id'], res, model)
        else:
            logging.error(
                f"Failed to infer analysis for {task['case_id']}")
            
def sanitizer_detection_p2(proj, model, temperature=1.0, max_tokens=2048, range_start=0, range_end=None, max_iters=1):
    prompts = PROMPT['sanitizer_detection_p2']
    bug_groups = proj.bug_groups

    # bug_groups = bug_groups[6:10]
    if range_end is None:
        range_end = len(bug_groups)
    bug_groups = bug_groups[range_start:range_end]

    # for bug_group in bug_groups:
    for bug_group in track(bug_groups, description="Sanitizer detection"):
        # filter: if "smart bug analysis" is not "bug", the skip:
        if __is_false_alarm_by_analysis(f"{proj.proj_id}:{bug_group.group_id:04d}", model):
            continue
        
        context = bug_group.get_last_context()
        task = {"id": "sanitizer_detection_p2", "proj_dir": proj.proj_dir,
                "context": context, "case_id": f"{proj.proj_id}:{bug_group.group_id:04d}"}
        res = run_with_majority_voting(
            context, prompts, task, model, temperature, max_tokens, 'res', task['case_id'], max_iters)
        if res:
            insert_or_update_sanitizer(task['case_id'], res, model)
        else:
            logging.error(
                f"Failed to infer analysis for {task['case_id']}")