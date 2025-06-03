# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)