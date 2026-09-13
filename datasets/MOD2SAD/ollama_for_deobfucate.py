import time
import subprocess
from collections import deque
from langchain_ollama import OllamaLLM
from langchain_core.callbacks import CallbackManager
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


MAX_OUTPUT_CHARS = 60000          
REPETITION_TAIL_LEN = 600         
REPETITION_KGRAM = 40             
REPETITION_MAX_HITS = 8           
STREAM_IDLE_TIMEOUT = 120          
HARD_WALL_TIME = 300               


def _ollama_stop(model_name):
    try:
        subprocess.run(
            ["ollama", "stop", model_name],
            check=False,
            timeout=15,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[Warning] ollama stop {model_name} failed: {e}")


def _looks_like_repetition(tail_buffer):
    if len(tail_buffer) < REPETITION_KGRAM * REPETITION_MAX_HITS:
        return False
    s = ''.join(tail_buffer)
    probe = s[-REPETITION_KGRAM:]
    return s.count(probe) >= REPETITION_MAX_HITS


def stream_querry_llm(llm_model, prompt):
    start_time = time.time()
    llm = OllamaLLM(
        model=llm_model,
        callbacks=CallbackManager([StreamingStdOutCallbackHandler()]),
        num_ctx=31268,
        num_predict=-1,
        temperature=0.1,
        top_p=0.9,
        repeat_penalty=1.2,
        num_thread=16,
        num_gpu=18,
        base_url='http://localhost:11434',
        repeat_last_n=256,
    )

    output_parts = []
    output_len = 0
    tail_buf = deque(maxlen=REPETITION_TAIL_LEN)
    last_chunk_time = time.time()
    abort_reason = None
    stream_iter = llm.stream(prompt)

    try:
        for chunk in stream_iter:
            now = time.time()

            if now - start_time > HARD_WALL_TIME:
                abort_reason = f"wall_time>{HARD_WALL_TIME}s"
                break

            if now - last_chunk_time > STREAM_IDLE_TIMEOUT:
                abort_reason = f"idle>{STREAM_IDLE_TIMEOUT}s"
                break
            last_chunk_time = now

            output_parts.append(chunk)
            output_len += len(chunk)
            tail_buf.extend(chunk)

            if output_len > MAX_OUTPUT_CHARS:
                abort_reason = f"output>{MAX_OUTPUT_CHARS}chars"
                break

            if output_len > REPETITION_TAIL_LEN and _looks_like_repetition(tail_buf):
                abort_reason = "repetition_detected"
                break
    except Exception as e:
        abort_reason = f"stream_exception:{type(e).__name__}:{e}"
    finally:
        try:
            stream_iter.close()
        except Exception:
            pass

    if abort_reason is not None:
        print(f"\n[LLM protection mechanism triggered] reason={abort_reason}, {output_len} characters have been output, calling ollama stop {llm_model}")
        _ollama_stop(llm_model)

    output = ''.join(output_parts)
    end_time = time.time()
    comsume_time = end_time - start_time
    completion_tokens = len(output)
    prompt_tokens = len(prompt)
    all_tokens = completion_tokens + prompt_tokens

    return output, completion_tokens, prompt_tokens, all_tokens, comsume_time