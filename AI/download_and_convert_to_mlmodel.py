from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import coremltools as ct
import os

# Updated to the requested model
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

# Load tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model with Apple Silicon optimizations
print("Loading model with Apple Silicon optimizations...")
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,  # Use FP16 which is optimal for M-series chips
    low_cpu_mem_usage=True,
    device_map="auto"
)
model.eval()

# Define optimized forward function for Apple Silicon
def optimized_forward(input_ids):
    with torch.no_grad():
        outputs = model(input_ids)
    return outputs.logits

# Use example input with batch size optimization for Metal
print("Preparing for model conversion...")
prompt = "Hello"
inputs = tokenizer(prompt, return_tensors="pt")
input_ids = inputs["input_ids"].to(model.device)

# Trace the model with better optimization flags
print("Tracing model...")
with torch.no_grad():
    traced_model = torch.jit.trace(optimized_forward, input_ids, check_trace=False)

# Convert to CoreML with Apple Silicon optimizations
print("Converting to CoreML with Apple Silicon optimizations...")
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.TensorType(name="input_ids", shape=(1, None), dtype=int)],
    compute_units=ct.ComputeUnit.ALL,  # Uses Neural Engine, GPU and CPU
    minimum_deployment_target=ct.target.macOS15,  # Target newer macOS for best performance
    convert_to="mlprogram",  # More efficient on Apple Silicon
    compute_precision=ct.precision.FLOAT16  # Half precision for Apple Silicon
)

# Additional ML Program optimizations for Apple Silicon
mlmodel.user_defined_metadata["com.apple.coreml.model.precision"] = "float16"
mlmodel.short_description = "Optimized for Apple Silicon"

# Updated output filename
print("Saving optimized model...")
mlmodel.save("DeepSeekR1DistillQwen.mlmodel", compress=True)

# Report model size
model_size = os.path.getsize("DeepSeekR1DistillQwen.mlmodel") / (1024 * 1024)
print(f"Model size: {model_size:.2f} MB")