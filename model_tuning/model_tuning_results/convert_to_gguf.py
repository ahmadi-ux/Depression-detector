import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os
import argparse

def _is_adapter_dir(path):
    if not os.path.isdir(path):
        return False

    has_config = os.path.isfile(os.path.join(path, "adapter_config.json"))
    has_weights = any(
        os.path.isfile(os.path.join(path, name))
        for name in ("adapter_model.safetensors", "adapter_model.bin")
    )
    return has_config and has_weights


def resolve_final_model_path(user_path):
    cleaned = user_path.strip().strip('"').strip("'")
    resolved = os.path.abspath(cleaned)

    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Training run path does not exist: {resolved}")

    if os.path.isfile(resolved):
        raise ValueError("Provide a folder path, not a file path.")

    final_model_dir = os.path.join(resolved, "final_model")

    if not os.path.isdir(final_model_dir):
        raise ValueError(f"Could not find final_model folder at: {final_model_dir}")

    if not _is_adapter_dir(final_model_dir):
        raise ValueError(
            "final_model folder is missing adapter files. "
            "Expected adapter_config.json and adapter_model.safetensors or adapter_model.bin."
        )

    return final_model_dir


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge LoRA adapter from final_model into base model and convert to GGUF."
    )
    parser.add_argument(
        "input_folder",
        help="Path to the training run folder that contains final_model."
    )
    parser.add_argument(
        "output_folder",
        help="Name or path of output folder for merged model and GGUF files."
    )
    return parser.parse_args()


# 1. Define paths
base_model_path = "meta-llama/Llama-3.1-8B" # or HF ID like "meta-llama/Llama-2-7b-hf"

args = parse_args()

adapter_path = resolve_final_model_path(args.input_folder)
print(f"Using adapter path: {adapter_path}")

output_folder = args.output_folder.strip().strip('"').strip("'")
if not output_folder:
    raise ValueError("Output folder name cannot be empty.")

output_path = os.path.abspath(output_folder)

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    dtype=torch.float16,
    device_map="cpu"  # Merging is RAM-intensive, CPU is fine
)

print("Loading adapter and merging...")
model = PeftModel.from_pretrained(base_model, adapter_path)
merged_model = model.merge_and_unload() #

print(f"Saving merged model to {output_path}...")
merged_model.save_pretrained(output_path, safe_serialization=True)

# Also save the tokenizer to the same folder
tokenizer = AutoTokenizer.from_pretrained(base_model_path)
tokenizer.save_pretrained(output_path)
print("Done!")

from llama_cpp import convert_hf_to_gguf

# ensure the gguf output directory exists
gguf_dir = output_path
os.makedirs(gguf_dir, exist_ok=True)

gguf_filename = f"{os.path.basename(os.path.normpath(output_path))}.gguf"

convert_hf_to_gguf(
    model_path_or_name=output_path,
    output_dir=gguf_dir,
    output_filename=gguf_filename,
    outtype="f16"
)
print("Done!")