import os
from datetime import datetime
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    TrainerCallback,
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
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, hamming_loss
import pandas as pd
import numpy as np

# hard‑coded values (replace with args or config as needed)
MODEL_NAME = "meta-llama/Llama-3.1-8B"
HF_TOKEN = ""  # set to your Hugging Face token if needed for private models


EMOTION_LIST = ['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 
                'loneliness', 'sadness', 'suicide intent', 'worthlessness']

def parse_binary_string(pred_str, expected_len=8):
    """Extract a valid 8-char binary string from model output, with fallback."""
    cleaned = pred_str.strip().replace(" ", "")
    # Find the first 8-char substring of only 0s and 1s
    for i in range(len(cleaned)):
        candidate = cleaned[i:i + expected_len]
        if len(candidate) == expected_len and all(c in "01" for c in candidate):
            return candidate
    return "0" * expected_len  # fallback: no emotions detected


def predict_label(text, model, tokenizer, max_new_tokens=8):
    prompt = (
        "Classify whether the following text indicates depression. "
        "If depression is detected, indicate which of these emotions are present: emotion_list = ['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 'loneliness', 'sadness', 'suicide intent', 'worthlessness']"
        "Respond with ONLY a binary string that cooralates to which emotions are present.\nOUTPUT EXAMPLES:\n['emptiness', 'hopelessness'] -> 00110000\n['anger'] -> 10000000\n"
        "['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 'loneliness', 'sadness', 'suicide intent', 'worthlessness'] -> 11111111 \n\n"
        "TEXT:\n" + text + "\n\nLABEL:"
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(model.device)
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = output_tokens[0][inputs["input_ids"].shape[1]:]
    prediction = tokenizer.decode(new_tokens, skip_special_tokens=True).strip().lower()
    return parse_binary_string(prediction)


def binary_string_to_vec(s):
    """Convert '01101000' -> [False, True, True, False, True, False, False, False]."""
    return [c == "1" for c in s]


def run_inference(model, tokenizer, val_dataset):
    all_preds = []   # list of 8-int lists
    all_gold  = []   # list of 8-int lists
    raw_preds = []   # for printing mistakes
    model.eval()

    print(f"[INFO] Evaluating {len(val_dataset)} samples...")
    for i in range(len(val_dataset)):
        ex = val_dataset[i]
        gold_str = label_to_target(ex.get("label", 0))   # e.g. "00110000"
        pred_str = predict_label(ex["text"], model, tokenizer)

        all_gold.append(binary_string_to_vec(gold_str))
        all_preds.append(binary_string_to_vec(pred_str))
        raw_preds.append((gold_str, pred_str))

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(val_dataset)}...")

    gold_arr = np.array(all_gold)   # shape (N, 8)
    pred_arr = np.array(all_preds)  # shape (N, 8)

    # --- Per-emotion metrics ---
    print("\n--- Per-Emotion Classification Report ---")
    print(classification_report(
        gold_arr, pred_arr,
        target_names=EMOTION_LIST,
        zero_division=0,
    ))

    # --- Aggregate multi-label metrics ---
    exact_match = np.all(gold_arr == pred_arr, axis=1).mean()
    h_loss      = hamming_loss(gold_arr, pred_arr)
    print(f"Exact Match Accuracy : {exact_match:.4f}  (all 8 bits correct)")
    print(f"Hamming Loss         : {h_loss:.4f}  (fraction of wrong bits)")

    # Per-emotion accuracy
    per_emotion_acc = (gold_arr == pred_arr).mean(axis=0)
    print("\n--- Per-Emotion Bit Accuracy ---")
    for name, acc in zip(EMOTION_LIST, per_emotion_acc):
        print(f"  {name:<35} {acc:.4f}")

    # --- Confusion matrix per emotion ---
    print("\n--- Per-Emotion Confusion Matrices ---")
    for j, name in enumerate(EMOTION_LIST):
        cm = confusion_matrix(gold_arr[:, j], pred_arr[:, j], labels=[False, True])
        print(f"\n  {name}")
        cm_df = pd.DataFrame(
            cm,
            index=["Actual 0", "Actual 1"],
            columns=["Pred 0", "Pred 1"],
        )
        print(cm_df.to_string(index=True))

    # --- Sample mistakes ---
    print("\n--- Sample Mistakes (up to 10) ---")
    mistake_count = 0
    for i, (gold_str, pred_str) in enumerate(raw_preds):
        if gold_str != pred_str and mistake_count < 10:
            print(f"  Text  : {val_dataset[i]['text'][:100]}...")
            print(f"  Gold  : {gold_str}  ({_decode_bits(gold_str)})")
            print(f"  Pred  : {pred_str}  ({_decode_bits(pred_str)})")
            print("  " + "-" * 50)
            mistake_count += 1


def _decode_bits(bit_str):
    """Human-readable emotion names for a bit string, e.g. '10010000' -> 'anger, hopelessness'."""
    active = [EMOTION_LIST[i] for i, b in enumerate(bit_str) if b == "1"]
    return ", ".join(active) if active else "none"


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


emoDep = pd.read_json('data_sets/combined.json', lines=True)
emoDep = emoDep.rename(columns={"label_id": "label"}) #change column name to label
emoDep = emoDep.rename(columns={"text": "text"}) #no-op command can change

csv_file1 = pd.read_csv('data_sets/training_data.csv')
csv_file1 = csv_file1.rename(columns={"class": "label"}) #change column name to label
csv_file1 = csv_file1.rename(columns={"text": "text"}) #no-op command can change
#remove rows with label value 0 or 4. 0 = depressed, 4 = anxiety
#Also filter out low-confidence samples to improve data quality
csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= .80]
# Remaining classes in this source are non-emotion categories; map to no-emotion target.
csv_file1["label"] = "00000000"


#combine datasets by shared columns (text and label)
common_columns = ["text", "label"]
emoDep = emoDep[common_columns]
csv_file1 = csv_file1[common_columns]

# Ensure compatible schema for Dataset concatenation (both labels must be same type).
emoDep["label"] = emoDep["label"].astype(str).str.strip()
csv_file1["label"] = csv_file1["label"].astype(str).str.strip()

#combine datasets and create test split
dataset_csv1 = Dataset.from_pandas(csv_file1)
dataset_depEmo = Dataset.from_pandas(emoDep)


combined_dataset = concatenate_datasets([dataset_csv1, dataset_depEmo])
split = combined_dataset.train_test_split(test_size=0.1, seed=42)  # remember seed so we can pull out training data.
train_hf = split["train"]
val_hf = split["test"]


# Print count of entries with all-zero emotion label vs non-zero emotion labels.
count_zero = combined_dataset.filter(
    lambda x: str(x["label"]).strip().zfill(8) == "00000000"
).num_rows
count_non_zero = combined_dataset.filter(
    lambda x: str(x["label"]).strip().zfill(8) != "00000000"
).num_rows
print("Count with label 00000000:", count_zero)
print("Count with label not 00000000:", count_non_zero)
# show a sample and overall size from the concatenated Dataset
print("sample data entry:", combined_dataset[0])
print(f"[INFO] dataset size = {len(combined_dataset)} samples")


def label_to_target(label, expected_len=8):
    """Normalize dataset labels into fixed-length binary strings for gold targets."""
    value = str(label).strip()

    # Strict gold format: only 0/1 chars, then left-pad to exactly expected_len.
    if value and all(c in "01" for c in value) and len(value) <= expected_len:
        return value.zfill(expected_len)

    raise ValueError(f"Invalid multilabel target: {label}")



class DepressDataset(torch.utils.data.Dataset):
    def __init__(self, hf_dataset, tokenizer, max_length=2048): #make max_length larger than inputs + response
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
            "If depression is detected, indicate which of these emotions are present: emotion_list = ['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 'loneliness', 'sadness', 'suicide intent', 'worthlessness']"
            
            "Respond with ONLY a binary string that cooralates to which emotions are present.\nOUTPUT EXAMPLES:\n['emptiness', 'hopelessness'] -> 00110000\n['anger'] -> 10000000\n"
            "['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 'loneliness', 'sadness', 'suicide intent', 'worthlessness'] -> 11111111 \n\n"
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


class SampleProgressCallback(TrainerCallback):
    """Print training progress every N optimizer steps."""

    def __init__(self, every_n_steps=100):
        self.every_n_steps = every_n_steps
        self.next_report_step = every_n_steps

    def _latest_metrics(self, state):
        latest = state.log_history[-1] if state.log_history else {}
        loss = latest.get("loss")
        lr = latest.get("learning_rate")
        return loss, lr

    def _emit_if_needed(self, state):
        while state.global_step >= self.next_report_step and state.global_step > 0:
            loss, lr = self._latest_metrics(state)
            parts = [
                f"[TRAIN] step={self.next_report_step}",
            ]
            if loss is not None:
                parts.append(f"loss={loss:.6f}")
            if lr is not None:
                parts.append(f"lr={lr:.3e}")
            print(" | ".join(parts))
            self.next_report_step += self.every_n_steps

    def on_step_end(self, args, state, control, **kwargs):
        self._emit_if_needed(state)

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
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    logging_steps=100,
    logging_first_step=False,
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
    callbacks=[SampleProgressCallback(every_n_steps=100)],
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

