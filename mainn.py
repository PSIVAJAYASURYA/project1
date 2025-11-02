from huggingface_hub import InferenceClient
client = InferenceClient(model="meta-llama/Llama-3.2-1B-Instruct",
                         token="hf_your_token_here")
print(client.text_generation("hello", max_new_tokens=10))
