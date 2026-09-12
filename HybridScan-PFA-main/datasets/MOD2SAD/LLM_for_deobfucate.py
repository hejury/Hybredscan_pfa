import requests
import json
import os
from openai import OpenAI
import time

def deal_obfu_llm(model,prompt):
    print(f"Start to invoke the LLM for disambiguation")
    deo_start_time = time.time()
    llm_output,completion_tokens,prompt_tokens,total_tokens = LLM_query(model,prompt,thinking_budget=None)
    deo_end_time = time.time() 
    deobfucate_time = (deo_end_time - deo_start_time)
    return llm_output,completion_tokens,prompt_tokens,total_tokens,deobfucate_time

def LLM_query(modelname,query,thinking_budget):
    client = OpenAI(
        api_key='your_api_key',
        base_url="your_api_base_url"
    )

    completion = client.chat.completions.create(
        # model = 'qwen3-235b-a22b-thinking-2507',
        model = modelname,
        messages = [
            {"role": "user", "content": query}
        ],
        stream=True,
        stream_options={"include_usage": True}, 
        temperature=0,
        top_p=0.1,
        presence_penalty = 1.5,
        response_format={"type": "text"},
        max_tokens=32768,
        extra_body={
            'top_k':1,
            'enable_search':False, 
            "thinking_budget": 32768/2 
            },
        stop=["Resolution of confusion completed"], 
    )

    llm_output = ''
    for line in completion:
        dump_chunk = (line.model_dump())
        if dump_chunk['choices']:
            content_chunk = dump_chunk['choices'][0]['delta']['content']
            # reason_chunk = dump_chunk['choices'][0]['delta']['reasoning_content']
            if content_chunk:
                llm_output+=content_chunk
                # print(content_chunk,end='',flush=True) 
            # if reason_chunk:
            #     print(reason_chunk,end='',flush=True)
        else:
            completion_tokens = dump_chunk['usage']['completion_tokens']
            prompt_tokens = dump_chunk['usage']['prompt_tokens']
            total_tokens = dump_chunk['usage']['total_tokens']

    # print(f"llm_output:{llm_output}")
    return llm_output,completion_tokens,prompt_tokens,total_tokens
