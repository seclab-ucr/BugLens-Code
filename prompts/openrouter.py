import os
import requests
from time import sleep

# openrouter_api_key
__openrouter_dir = "../openrouter.key"
if 'OPENROUTER_API_KEY' not in os.environ:
    with open(__openrouter_dir, "r") as f:
        __openrouter_api_key = f.read().strip()
else:
    __openrouter_api_key = os.environ['OPENROUTER_API_KEY']
__headers = {
    'Authorization': 'Bearer ' + __openrouter_api_key,
    'X-Title': 'LMSuture',
    'Content-Type': 'application/json',
}


def open_router_request_single_provider(formatted_msg, model, provider, retry=0, max_retry=3, retry_timeout=[1, 2, 4], last_error=None):
    sleep(1)
    try:
        response = requests.post('https://openrouter.ai/api/v1/chat/completions',
                                 headers=__headers, json={
                                     'model': model,
                                     'messages': formatted_msg,
                                     'provider': {
                                         'order': [
                                             provider,
                                         ],
                                         'allow_fallbacks': False
                                     }
                                 })
        res = response.json()
    except Exception as e:
        e_msg = str(e)
        if e_msg == last_error:
            return "Same Error: " + e_msg
        if retry < max_retry:
            sleep(retry_timeout[retry])
            return open_router_request_single_provider(formatted_msg, model, provider, retry + 1, max_retry, retry_timeout, e_msg)
    if not res or 'error' in res:
        if not res or 'error' not in res:
            err_msg = "No Response"
        else:
            err_msg = res['error']['message']
        if err_msg == last_error:
            return "Same Error: " + err_msg
        if retry < max_retry:
            sleep(retry_timeout[retry])
            return open_router_request_single_provider(formatted_msg, model, provider, retry + 1, max_retry, retry_timeout, err_msg)
    
    return res['choices'][0]['message']['content']
    


if __name__ == "__main__":
    formatted_msg = [{
        "role": "user",
        "content": "what is the meaning of life?"
    }]
    model = "gpt-4o"
    provider = "OpenAI"
    response = open_router_request_single_provider(
        formatted_msg, model, provider)
    print(response)
