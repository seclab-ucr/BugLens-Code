import logging
from time import sleep
import openai
import anthropic
import os
import re
import xml.etree.ElementTree as ET

# from helper.get_func_def import get_func_def
from helper.dao import insert_log, find_case_varname, find_analysis_result, get_req_sanitizer, get_detected_sanitizer
import helper.callbacks as cb

from prompts.openrouter import open_router_request_single_provider

import read_result as rr
import ollama

__CALLBACK_ITER_MAX_LIMIT = 15
__API_RETRY_LIMIT = 3
__RETRY_TIMEOUT = [60, 120, 300]

api_key = "../openai.key"
if 'OPENAI_API_KEY' not in os.environ:
    if os.path.exists(api_key):
        key_chain = open(api_key, 'r').read().splitlines()[0]
        os.environ['OPENAI_API_KEY'] = key_chain

claude_api_key = "../claude.key"
if 'ANTHROPIC_API_KEY' not in os.environ:
    if os.path.exists(claude_api_key):
        key_chain = open(claude_api_key, 'r').read().splitlines()[0]
        os.environ['ANTHROPIC_API_KEY'] = key_chain
__claude_client = anthropic.Anthropic()

deepseek_api_key = "../deepseek.key"
if 'DEEPSEEK_API_KEY' not in os.environ:
    if os.path.exists(deepseek_api_key):
        key_chain = open(deepseek_api_key, 'r').read().splitlines()[0]
        os.environ['DEEPSEEK_API_KEY'] = key_chain
__deepseek_clinet = openai.OpenAI(
    api_key=os.environ['DEEPSEEK_API_KEY'], base_url="https://api.deepseek.com")

gemini_api_key = "../gemini.key"
if 'GEMINI_API_KEY' not in os.environ:
    if os.path.exists(gemini_api_key):
        key_chain = open(gemini_api_key, 'r').read().splitlines()[0]
        os.environ['GEMINI_API_KEY'] = key_chain
__gemini_client = openai.OpenAI(
    api_key=os.environ['GEMINI_API_KEY'], base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

# def _get_tainted_value(task):
#     case = find_case_varname(task["case_id, ctx.model)
#     if case and case[0]:
#         return case[0]


def get_from_response(response, xml_tag='response'):
    pattern = f'<{xml_tag}>(.*?)</{xml_tag}>'
    match = re.search(pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None


def get_request_list(response):
    response = f"<root>{response}</root>"
    try:
        root = ET.fromstring(response)
        request_list = []
        for req in root.findall('request'):
            req_name = req.find('name').text
            args_elem = req.find('args').findall('arg')
            args = [arg.text for arg in args_elem]
            request_list.append({'name': req_name, 'args': args})

        return request_list

    except Exception as e:
        logging.error(e)
        return []


def safe_get_first(lst):
    if lst:
        return lst[0]
    return None


ARGS_MAP = {
    'get_function': lambda task: rr.get_function(task['context'], task['proj_dir']),
    'get_function_second_part': lambda task: rr.get_function_second_part(task['context'], task['proj_dir']),
    'get_function_first_part': lambda task: rr.get_function_first_part(task['context'], task['proj_dir']),
    'get_insts_from_ctx': lambda task: rr.get_insts_from_ctx(task['context']),
    'get_source_line_set': lambda task: rr.get_source_line_set(task['context'], task['proj_dir']),
    'get_tainted_value': lambda task: safe_get_first(find_case_varname(task['case_id'], task['model'])),
    'get_bug_detector': lambda task: task['context'].desc,
    'get_analysis_result': lambda task: safe_get_first(find_analysis_result(task['case_id'], task['model'])),
    'get_call_chain': lambda task: ', '.join(task['context'].call_chain),
    'get_req_sanitizer': lambda task:  get_req_sanitizer(task['case_id'], task['model'])[0],
    'get_detected_sanitizer': lambda task: safe_get_first(get_detected_sanitizer(task['case_id'], task['model'])),
}

CALLBACKS = {
    'need_func_def': cb.function_retrieve_callback,
    'need_caller': cb.caller_retrieve_callback,
    'need_struct_def': cb.struct_retrieve_callback,
    'need_global_var_def': cb.global_var_retrieve_callback,
}


def _ollama_do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    try:
        response: ollama.ChatResponse = ollama.chat(model=model, messages=formatted_messages)
        res = response['message']['content']
        # if <think> xxx </think> in the response, remove it
        res = re.sub(r'<think>.*?</think>', '', res, flags=re.DOTALL)
        
    except Exception as e:
        logging.error(e)
        emsg = str(e)

        if last_emsg is not None and emsg[:60] == last_emsg[:60]:
            logging.info("Same error")
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

        if _retry < __API_RETRY_LIMIT and ("context_length_exceeded" not in emsg):
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _ollama_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, emsg)
        else:
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

    return res

def _gemini_do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    try:
        completion = __gemini_client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            n=1
        )
    except Exception as e:
        logging.error(e)
        emsg = str(e)

        if last_emsg is not None and emsg[:60] == last_emsg[:60]:
            logging.info("Same error")
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

        if _retry < __API_RETRY_LIMIT and ("context_length_exceeded" not in emsg):
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _gemini_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, emsg)
        else:
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

    return completion.choices[0].message.content

def _oai_do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    try:
        # if model has "deepseek" in it, use deepseek API
        if "deepseek" in model:
            completion = __deepseek_clinet.chat.completions.create(
                model=model,
                messages=formatted_messages,
                max_tokens=max_tokens,
                stream=False,
            )
            # if 'reasoning_content' in completion.choices[0].message:
            reasoning_content = getattr(
                completion.choices[0].message, 'reasoning_content', None)
            if reasoning_content:
                logging.info(
                    f"Deepseek API reasoning content: {reasoning_content}")
        else:
            completion = openai.chat.completions.create(
                model=model,
                messages=formatted_messages,
            )

    except Exception as e:
        logging.error(e)
        emsg = str(e)

        if last_emsg is not None and emsg[:60] == last_emsg[:60]:
            logging.info("Same error")
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

        if _retry < __API_RETRY_LIMIT and ("context_length_exceeded" not in emsg):
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, emsg)
        else:
            return '{"ret": "failed", "response": "' + emsg[:200] + '"}'

    return completion.choices[0].message.content

def _claude_beta_do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    try:
        # ststem_prompt = formatted_messages[0]['content']
        # if len(formatted_messages) > 1:
        #     formatted_messages = formatted_messages[1:]
        # else:
        #     formatted_messages = [
        #         {
        #             "role": "user",
        #             "content": "Let's start the analysis: \n"
        #         }
        #     ]
        
        formatted_messages[0]['cache_control'] = {"type": "ephemeral"}
        message = __claude_client.beta.messages.create(
            model=model,
            max_tokens=128000,
            thinking={
                "type": "enabled",
                "budget_tokens": 32000
            },
            messages=formatted_messages, 
            betas=["output-128k-2025-02-19"])
    
    except Exception as e:
        msg = str(e)
        logging.error(e)
        if _retry < __API_RETRY_LIMIT and msg != last_emsg:
            # sleep(1)
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, str(e))
        else:
            logging.error(f"Failed to call Claude API for many times")
            return '{"ret": "failed", "response": "' + msg + '"}'

    if message.content[0].type == "error" and ("exceeded" not in message.content[0].text):
        logging.info(
            f"no excpetion but return with 'error' type: {message.content[0].text}")
        if _retry < __API_RETRY_LIMIT and message.content[0].text != last_emsg:
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, message.content[0].text)

        return '{"ret": "failed", "response": "' + message.content[0].text + '"}'
    return message.content[0].text

def _claude_beta_do_request_streaming(
    model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None
):
    """
    Example streaming function using the official doc approach.
    """
    try:
        # If ephemeral usage is causing no content, try removing this
        # formatted_messages[0]["cache_control"] = {"type": "ephemeral"}

        with __claude_client.beta.messages.stream(
            model=model,
            max_tokens=128000,
            thinking={"type": "enabled", "budget_tokens": 32000},
            messages=formatted_messages,
            betas=["output-128k-2025-02-19"],
            # temperature=temperature,  # optionally use if you want
        ) as stream:

            # Accumulate partial chunks
            all_text_parts = []

            # Iterate over partial text
            for partial_text in stream.text_stream:
                all_text_parts.append(partial_text)

        # Combine into final response string
        full_response = "".join(all_text_parts)

        return full_response

    except Exception as e:
        msg = str(e)
        logging.error(e)
        # For demonstration, simple retry logic:
        if _retry < __API_RETRY_LIMIT and msg != last_emsg:
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _claude_beta_do_request_streaming(
                model, temperature, max_tokens, formatted_messages, _retry + 1, msg
            )
        else:
            logging.error("Failed to call Claude API many times")
            return '{"ret": "failed", "response": "' + msg + '"}'

def _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    try:
        ststem_prompt = formatted_messages[0]['content']
        if len(formatted_messages) > 1:
            formatted_messages = formatted_messages[1:]
        else:
            formatted_messages = [
                {
                    "role": "user",
                    "content": "Let's start the analysis: \n"
                }
            ]

        message = __claude_client.messages.create(
            max_tokens=max_tokens,
            model=model,
            # temperature=0.2,
            system=[
                {
                    "type": "text",
                    "text": "You are an expert in C and Linux kernel, help me finish the following analysis.\n",
                },
                {
                    "type": "text",
                    "text": ststem_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=formatted_messages,
        )
    except Exception as e:
        msg = str(e)
        if _retry < __API_RETRY_LIMIT and msg != last_emsg:
            # sleep(1)
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, str(e))
        else:
            logging.error(f"Failed to call Claude API: {msg}")
            return '{"ret": "failed", "response": "' + msg + '"}'

    if message.content[0].type == "error" and ("exceeded" not in message.content[0].text):
        logging.info(
            f"no excpetion but return with 'error' type: {message.content[0].text}")
        if _retry < __API_RETRY_LIMIT and message.content[0].text != last_emsg:
            sleep(__RETRY_TIMEOUT[_retry])
            logging.info(f"Retrying {_retry + 1} time(s)...")
            return _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry + 1, message.content[0].text)

        return '{"ret": "failed", "response": "' + message.content[0].text + '"}'

    return message.content[0].text


def _do_request(model, temperature, max_tokens, formatted_messages, _retry=0, last_emsg=None):
    sleep(0.2)  # avoid rate limit
    if "--" in model:
        model = model.split("--")[0]

    if model.startswith("ollama/"):
        model = model[7:]
        return _ollama_do_request(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)
    elif model.startswith("openrouter/"):
        model = model[11:]
        provider = model.split("/")[0]
        model = model[len(provider) + 1:]
        return open_router_request_single_provider(formatted_messages, model, provider, _retry, __API_RETRY_LIMIT, __RETRY_TIMEOUT)
    elif "claude" in model:
        if "claude-3-7-sonnet" in model:
            # return _claude_beta_do_request(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)
            return _claude_beta_do_request_streaming(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)
        return _claude_do_request(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)
    elif "gemini" in model:
        return _gemini_do_request(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)
    else:
        return _oai_do_request(model, temperature, max_tokens, formatted_messages, _retry, last_emsg)


def __is_failed(response):
    return response.startswith('{"ret": "failed"')


def do_request_llm(model, temperature, max_tokens, formatted_messages, cur_prompt, round='N/A', case_id='N/A'):
    # formatted_messages.append({"role": "system", "content": cur_prompt})
    response = _do_request(model, temperature, max_tokens, formatted_messages)
    logging.info(f"Round: {round}, Case {case_id}, Response: {response}")
    insert_log(cur_prompt, response, model, round, case_id)
    return response


def get_params(args, task):
    res = []
    for arg in args:
        if arg in ARGS_MAP:
            ret = ARGS_MAP[arg](task)
            if ret is None:
                return None
            res.append(ret)
        else:
            raise ValueError(f"Unknown arg: {arg}")
    return res


def do_request_series(model, temperature, max_tokens, prompts, task):
    formatted_messages = []
    task_id = task['id']
    case_id = task['case_id']
    task['model'] = model
    
    cb.clear_counter()

    # prompts[0] = prompts[0].format(**init_info)
    for index, cur_prompt in enumerate(prompts):
        if task_id != 'N/A':
            round = 'Task ' + task_id + ' - ' + str(index + 1)
        else:
            round = 'N/A'
        if 'args' in cur_prompt:
            params = get_params(cur_prompt['args'], task)
            if params is None:
                logging.error(f"Failed to get params for {cur_prompt['args']}")
                return None

            prompt = cur_prompt['text'].format(*params)
        else:
            prompt = cur_prompt['text']

        # handle callbacks
        for cb_iter in range(__CALLBACK_ITER_MAX_LIMIT):
            formatted_messages.append({"role": "user", "content": prompt})
            ret = do_request_llm(model, temperature, max_tokens,
                                 formatted_messages, prompt, round, case_id)
            formatted_messages.append({"role": "assistant", "content": ret})

            if __is_failed(ret):
                return None

            call_back_finished = True

            # construct the new prompt for the next iteration
            prompt = ""
            if 'callback' in cur_prompt:

                # Update: now get the list of requests from the response
                requests_body = get_from_response(ret, 'requests')

                if requests_body:
                    request_list = get_request_list(requests_body)
                    if not request_list:
                        logging.error(
                            "Failed to parse request list from response.")
                        # tells LLM we don't understand the request
                        call_back_finished = False
                        prompt = "I don't understand your request, please request as the format\n"

                    for request in request_list:
                        callback = request['name']
                        if callback in CALLBACKS:
                            response = CALLBACKS[callback].call(
                                task, request['args'])
                            call_back_finished = False
                            prompt += response
                        else:
                            logging.error(
                                "Callback function {} not found.".format(callback))
                            break

            round = 'Task ' + task_id + ' - ' + \
                str(index + 1) + " - callback - " + str(cb_iter + 1)
            if call_back_finished:
                break

    return formatted_messages
