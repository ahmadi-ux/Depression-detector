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
from datasets import (
    load_dataset,
    concatenate_datasets,
    Dataset,
)
import pandas as pd
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

# --- inference / evaluation utilities ---
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pandas as pd


def predict_label(text, model, tokenizer, max_new_tokens=8):
    prompt = (
        "Classify whether the following text indicates depression. "
        "Respond with exactly 'depressed' or 'not-depressed'.\n\n"
        "TEXT:\n" + text + "\n\nLABEL:"
    )
    # max_length and truncation to prevent over long texts: thye dont pad each sample to maxL
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
        gold_label = label_to_target(ex.get("label", ex.get("label", 0)))
        pred_label = predict_label(ex["text"], model, tokenizer)
        pred_clean = pred_label.strip().lower()
        all_preds.append(pred_clean)
        all_gold.append(gold_label)
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(val_dataset)}...")

    print("\n--- Classification Report ---")
    labels = ["depressed", "not-depressed"]
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

# hard‑coded values (replace with args or config as needed)
MODEL_NAME = "meta-llama/Llama-3.1-8B"
HF_TOKEN = ""

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

def is_tf32_supported():
    """Return True only when torch/cuda/device support TF32 matmul."""
    if not torch.cuda.is_available():
        return False
    if torch.version.cuda is None:
        return False
    major, _minor = torch.cuda.get_device_capability(torch.cuda.current_device())
    return major >= 8

def is_bf16_supported():
    """Return True when BF16 is supported on this CUDA/PyTorch/device stack."""
    if not torch.cuda.is_available():
        return False
    if torch.version.cuda is None:
        return False
    major, _minor = torch.cuda.get_device_capability(torch.cuda.current_device())
    if major < 8:
        return False
    # Prefer PyTorch helper if available
    try:
        return torch.cuda.is_bf16_supported()
    except Exception:
        return True

def select_precision_for_device():
    """Return a dict with best precision flags for this device.

    - BF16 only enabled on Ampere+ (compute capability >= 8) when supported.
    - FP16 is used as a fallback for Turing/Volta (compute capability >= 7) when BF16 is not available.
    """
    if not torch.cuda.is_available():
        return {"bf16": False, "fp16": False}
    try:
        major, _ = torch.cuda.get_device_capability(torch.cuda.current_device())
    except Exception:
        major = 0

    bf16 = major >= 8 and getattr(torch.cuda, "is_bf16_supported", lambda: False)()
    fp16 = not bf16 and major >= 7
    return {"bf16": bf16, "fp16": fp16}

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


class CausalLMCollator:
    def __init__(self, tokenizer, label_pad_token_id=-100):
        self.tokenizer = tokenizer
        self.label_pad_token_id = label_pad_token_id

    def __call__(self, features):
        labels = [f["labels"] for f in features]
        token_features = [
            {"input_ids": f["input_ids"], "attention_mask": f["attention_mask"]}
            for f in features
        ]

        batch = self.tokenizer.pad(
            token_features,
            padding=True,
            return_tensors="pt",
        )

        seq_len = batch["input_ids"].shape[1]
        padded_labels = [
            label + [self.label_pad_token_id] * (seq_len - len(label)) for label in labels
        ]
        batch["labels"] = torch.tensor(padded_labels, dtype=torch.long)
        return batch


data_collator = CausalLMCollator(tokenizer=tokenizer)

# load dataset from csv provided in repo
#uniform mapping
# labels = label, 0 is depressed, all others are not-depressed
# text = text
emoDep = pd.read_json('data_sets/combined.json', lines=True)
emoDep = emoDep.rename(columns={"label_id": "label"}) #change column name to label
emoDep['label'] = 0 # Change all values in the 'label_id' column to 0 (depressed)
emoDep = emoDep.rename(columns={"text": "text"}) #no-op command can change

csv_file1 = pd.read_csv('data_sets/training_data.csv')
csv_file1 = csv_file1.rename(columns={"class": "label"}) #change column name to label
csv_file1 = csv_file1.rename(columns={"text": "text"}) #no-op command can change
#remove rows with label value 0 or 4. 0 = depressed, 4 = anxiety
#Also filter out low-confidence samples to improve data quality
csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= .80]

RMHD_1 = pd.read_csv('data_sets/labelled_file1.csv')
RMHD_2 = pd.read_csv('data_sets/labelled_file2.csv')
RMHD_3 = pd.read_csv('data_sets/labelled_file3.csv')
RMHD_4 = pd.read_csv('data_sets/labelled_file4.csv')
RMHD_1['label'] = 0  # Change all values in the 'label' column to 0 (depressed)
RMHD_2['label'] = 0
RMHD_3['label'] = 0
RMHD_4['label'] = 0

#combine datasets by shared columns (text and label)
common_columns = ["text", "label"]
emoDep = emoDep[common_columns]
csv_file1 = csv_file1[common_columns]

#combine datasets and create test split
dataset_csv1 = Dataset.from_pandas(csv_file1)
dataset_depEmo = Dataset.from_pandas(emoDep)
dataset_RMHD_1 = Dataset.from_pandas(RMHD_1)
dataset_RMHD_2 = Dataset.from_pandas(RMHD_2)
dataset_RMHD_3 = Dataset.from_pandas(RMHD_3)
dataset_RMHD_4 = Dataset.from_pandas(RMHD_4)

#13,636 samples total, 6,315 depressed (label 0) and 7,321 not-depressed
combined_dataset = concatenate_datasets([dataset_csv1, dataset_depEmo, dataset_RMHD_1, dataset_RMHD_2, dataset_RMHD_3, dataset_RMHD_4])
split = combined_dataset.train_test_split(test_size=0.1, seed=42)  # remember seed so we can pull out training data.
train_hf = split["train"]
val_hf = split["test"]


# Print count of entries with label 0 (depressed)
print("Count with label 0:", combined_dataset.filter(lambda x: x['label'] == 0).num_rows)
print("Count with label not 0:", combined_dataset.filter(lambda x: x['label'] != 0).num_rows)
# show a sample and overall size from the concatenated Dataset
print("sample data entry:", combined_dataset[0])
print(f"[INFO] dataset size = {len(combined_dataset)} samples")

# label 0 -> "depressed"
# label not 0 -> "not-depressed"
def label_to_target(label):
    try:
        l = int(label)
    except Exception:
        # raise error so calling code can detect bad input
        raise ValueError("DATA READING ERROR")
    if l == 0:
        return "depressed"
    elif l != 0:
        return "not-depressed"


class DepressDataset(torch.utils.data.Dataset):
    def __init__(self, hf_dataset, tokenizer, max_length=300): #make max_length larger than inputs + response
        self.hf = hf_dataset
        self.tok = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.hf)

    def __getitem__(self, idx):
        item = self.hf[idx]
        text = item.get("text", "")
        tgt = label_to_target(item.get("label", item.get("label", 0)))

        prompt = (
            "Classify whether the following text indicates depression. "
            "Respond with exactly 'depressed' or 'not-depressed'.\n\n"
            "TEXT:\n" + text + "\n\nLABEL:"
        )
        full = f"{prompt} {tgt}{self.tok.eos_token}"

        # tokenize without returning tensors so the collator can pad correctly
        enc = self.tok(
            full,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        input_ids = enc["input_ids"]
        attn = enc["attention_mask"]

        # create labels and mask prompt portion
        labels = input_ids.copy()
        prompt_ids = self.tok(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )["input_ids"]
        plen = len(prompt_ids)
        labels[:plen] = [-100] * plen

        # return plain Python lists (not torch tensors) so the default data_collator
        # can pad/truncate them without mismatched shapes
        return {"input_ids": input_ids, "attention_mask": attn, "labels": labels}

train_dataset = DepressDataset(train_hf, tokenizer)
eval_dataset = DepressDataset(val_hf, tokenizer)

# run baseline evaluation before training
print("[INFO] running baseline inference (untrained model)")
run_inference(model, tokenizer, val_hf)

tf32_enabled = is_tf32_supported()
if tf32_enabled:
    print("[INFO] TF32 enabled")
else:
    print("[INFO] TF32 disabled (unsupported GPU/CUDA stack)")

bf16_enabled = is_bf16_supported()
if bf16_enabled:
    print("[INFO] BF16 enabled")
else:
    print("[INFO] BF16 disabled (unsupported GPU/CUDA stack)")

# Choose precision flags appropriate for the current device
precision = select_precision_for_device()
print(f"[INFO] precision flags: bf16={precision['bf16']}, fp16={precision['fp16']}")

# training arguments optimized for H100
training_args = TrainingArguments(
    output_dir=f"llama3_depress_{timestamp}",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=4,
    num_train_epochs=5,
    bf16=precision["bf16"],
    fp16=precision["fp16"],
    warmup_steps=100,
    logging_steps=10,
    learning_rate=2e-5,
    save_total_limit=2,
    gradient_checkpointing=True,
    tf32=tf32_enabled,
    optim="adamw_torch_fused",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,
    data_collator=data_collator,
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

