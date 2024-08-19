import os
import time
import httpx
import shutil
import tiktoken
import requests
from openai import OpenAI


def encoding_getter(encoding_type: str):
    """
    Returns the appropriate encoding based on the given encoding type (either an encoding string or a model name).
    """
    if "k_base" in encoding_type:
        return tiktoken.get_encoding(encoding_type)
    else:
        return tiktoken.encoding_for_model(encoding_type)

def tokenizer(string: str, encoding_type: str) -> list:
    """
    Returns the tokens in a text string using the specified encoding.
    """
    encoding = encoding_getter(encoding_type)
    tokens = encoding.encode(string)
    return tokens

def token_counter(string: str, encoding_type: str) -> int:
    """
    Returns the number of tokens in a text string using the specified encoding.
    """
    num_tokens = len(tokenizer(string, encoding_type))
    return num_tokens

# class llm_client:
#     def __init__(self, url, name=None):
#         self.url = url
#         self.name = name

#     def model_info(self, keys=None):
#         response = requests.post(self.url + '/api/v1/model', json={'action': 'info'})
#         response = response.json()
#         print("Model: ", response['result']['model_name'])
#         print("Lora(s): ", response['result']['lora_names'])
#         if keys:
#             for setting in keys:
#                 print(setting, "=", response['result']['shared.settings'][setting])
#         else:
#             for setting in response['result']['shared.settings']:
#                 print(setting, "=", response['result']['shared.settings'][setting])        
    
#     def generate(self, question) -> (int, str):
#         llama_req = llama_param.copy()
#         llama_req['prompt'] = question
#         response = requests.post(self.url + '/api/v1/generate', json=llama_req)
#         if response.status_code == 200:
#             result = response.json()['results'][0]['text']
#             return 1,result
#         else:
#             return 0,None
            
#url1 = https://api.xiaoai.plus/v1
#url2 = aimlapi.com
# import ipdb
# model 1 for question with less token
class llm_client:
    def __init__(self, url, api_key, models=['gpt-3.5-turbo', 'gpt-3.5-turbo-16k'], token_model='gpt-3.5-turbo', token_threshold=4096, max_tokens=[1024, 4096], debug=False):
        self.client = OpenAI(
                    base_url=url, 
                    api_key=api_key,
                    http_client=httpx.Client(
                        base_url=url,
                        follow_redirects=True,
                    ),
                )
        if type(models) == list:
            assert len(models) == len(max_tokens)
        self.models = models
        self.token_model = token_model
        self.token_threshold = token_threshold
        self.max_tokens = max_tokens
        self.debug = debug

    def model_info(self, keys=None):
        model = self.client.models.retrieve(self.model)
        if model.__dict__:
            print(model.__dict__)
    
    def generate(self, question, temperature=0.4, max_repeat=3, debug=False):
        status,result,number_token,repeat_time = 0,None,0,0
        select_model,select_max_tok = 0,0
        number_token = token_counter(question, self.token_model)
        if type(self.models) == str:
            select_max_tok = self.max_tokens                
            select_model = self.models
        else:
            if number_token > self.token_threshold:
                select_max_tok = self.max_tokens[-1]                
                select_model = self.models[-1]
            else:
                select_max_tok = self.max_tokens[0]                
                select_model = self.models[0]
        for index in range(max_repeat): 
            try:
                completion = self.client.chat.completions.create(
                    model = select_model,
                    temperature = temperature,
                    max_tokens = select_max_tok,
                    frequency_penalty = 0,
                    presence_penalty = 0,
                    messages = [
                        {"role": "system", "content": "You are an AI assistant that helps people find information."},
                        {"role": "user", "content": question}
                    ]
                )
                response = completion.choices[0].message.content
                if self.debug:
                    print('request: ===================>')
                    print(question)
                    print('response: <==================')
                    print(response)
                status,result = 1,response
                break
            except Exception as err:
                if self.debug or debug:
                    print(err)
                    print('erroneous request: ===================>')
                    print(question)
                status,result = 0,str(err)
                repeat_time += 1
                time.sleep(0.5)
        return status,result,number_token,repeat_time  
        