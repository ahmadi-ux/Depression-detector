import os
from datetime import datetime

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
)
from datasets import load_dataset
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

# hard‑coded values (replace with args or config as needed)
MODEL_NAME = "meta-llama/Llama-3.1-8B"
HF_TOKEN = "" #PUT KEY TO ACCESS MODEL HERE

# --- inference / evaluation utilities ---
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pandas as pd

def predict_label(text, model, tokenizer, max_new_tokens=8):
    prompt = (
        "Classify whether the following text indicates depression. "
        "Respond with exactly 'depressed' or 'NA'.\n\n"
        "TEXT:\n" + text + "\n\nLABEL:"
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = output_tokens[0][inputs["input_ids"].shape[1] :]
    prediction = tokenizer.decode(new_tokens, skip_special_tokens=True).strip().lower()
    return prediction

def run_inference(model, tokenizer, val_dataset):

    all_preds = []
    all_gold = []
    model.eval()

    print(f"[INFO] Evaluating {len(val_dataset)} samples...")
    for i in range(len(val_dataset)):
        ex = val_dataset[i]
        gold_label = label_to_target(ex.get("labels", ex.get("label", 0)))
        pred_label = predict_label(ex["text"], model, tokenizer)
        pred_clean = pred_label.strip().lower()
        all_preds.append(pred_clean)
        all_gold.append(gold_label)
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(val_dataset)}...")

    print("\n--- Classification Report ---")
    labels = ["depressed", "na"]
    target_names = labels
    print(classification_report(all_gold, all_preds, labels=labels, target_names=target_names))
    acc = accuracy_score(all_gold, all_preds)
    print(f"Overall Accuracy: {acc:.4f}")

    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(all_gold, all_preds, labels=target_names)
    cm_df = pd.DataFrame(
        cm,
        index=[f"Actual {n}" for n in target_names],
        columns=[f"Predicted {n}" for n in target_names],
    )
    print(cm_df)

    print("\n--- Sample Mistakes ---")
    mistake_count = 0
    for i in range(len(all_gold)):
        if all_gold[i] != all_preds[i] and mistake_count < 10:
            print(f"Text: {val_dataset[i]['text'][:100]}...")
            print(f"Gold: {all_gold[i]} | Pred: {all_preds[i]}")
            print("-" * 30)
            mistake_count += 1


# timestamp so that multiple runs go to different dirs
timestamp = datetime.now().strftime("%m%d_%H%M%S")

# GPU diagnostics (H100 assumed)
if torch.cuda.is_available():
    device = torch.cuda.current_device()
    name = torch.cuda.get_device_name(device)
    props = torch.cuda.get_device_properties(device)
    print(f"GPU: {name} ({props.total_memory/1e9:.1f} GB)")
else:
    print("No CUDA device detected")

print("[INFO] loading tokenizer & model")
bnb_config = BitsAndBytesConfig(load_in_8bit=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    token=HF_TOKEN or None,
    quantization_config=bnb_config,
    device_map="auto",
)

# prepare for k-bit training and LoRA
model = prepare_model_for_kbit_training(model)
model.gradient_checkpointing_enable()
model.config.use_cache = False

peft_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, peft_cfg)
model.print_trainable_parameters()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN or None)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"[INFO] model loaded; dtype={model.dtype}")

# load dataset from csv provided in repo
dataset = load_dataset(
    "csv",
    data_files={"train": "data_sets/depression_reddit_cleaned_ds.csv"},
    delimiter=",",
    keep_default_na=False,
    token=HF_TOKEN or None,
)
print(f"[INFO] dataset size = {len(dataset['train'])} samples")

# label 0 -> "depressed" (note misspelling matches request)
# label 1 -> "NA"
def label_to_target(label):
    try:
        l = int(label)
    except Exception:
        # fallback in case of weird values
        l = 0
    return "depressed" if l == 0 else "NA"

# create train/val split (90% train, 10% test)
split = dataset["train"].train_test_split(test_size=0.1, seed=42)
train_hf = split["train"]
val_hf = split["test"]

class DepressDataset(torch.utils.data.Dataset):
    def __init__(self, hf_dataset, tokenizer, max_length=300): #longest in dataset is 177 tokens
        self.hf = hf_dataset
        self.tok = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.hf)

    def __getitem__(self, idx):
        item = self.hf[idx]
        text = item.get("text", "")
        tgt = label_to_target(item.get("labels", item.get("label", 0)))

        prompt = (
            "Classify whether the following text indicates depression. "
            "Respond with exactly 'depressed' or 'NA'.\n\n"
            "TEXT:\n" + text + "\n\nLABEL:"
        )
        full = f"{prompt} {tgt}{self.tok.eos_token}"

        enc = self.tok(
            full,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].squeeze(0)
        attn = enc["attention_mask"].squeeze(0)
        labels = input_ids.clone()

        # mask prompt tokens
        prompt_ids = self.tok(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors="pt",
        )["input_ids"].squeeze(0)
        plen = prompt_ids.shape[0]
        labels[:plen] = -100

        return {"input_ids": input_ids, "attention_mask": attn, "labels": labels}

train_dataset = DepressDataset(train_hf, tokenizer)
eval_dataset = DepressDataset(val_hf, tokenizer)

# run baseline evaluation before training
print("[INFO] running baseline inference (untrained model)")
run_inference(model, tokenizer, val_hf)

# training arguments optimized for H100
training_args = TrainingArguments(
    output_dir=f"llama3_depress_{timestamp}",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=4,
    num_train_epochs=5,
    bf16=True,
    warmup_steps=100,
    logging_steps=10,
    learning_rate=2e-5,
    save_total_limit=2,
    gradient_checkpointing=True,
    tf32=True,
    optim="adamw_torch_fused",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

print("[INFO] beginning training")
trainer.train()
trainer.save_model(f"llama3_depress_{timestamp}/final_model")
print("training complete")

# call inference after training
print("\n" + "=" * 50)
print("FINAL EVALUATION ON TEST DATA")
print("=" * 50)
run_inference(model, tokenizer, val_hf)

