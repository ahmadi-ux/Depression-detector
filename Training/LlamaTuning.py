from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import transformers
print(transformers.__version__)

# Load your data (assuming a JSON file with one dict per line)
dataset = load_dataset("json", data_files={"train": "Data.json", "validation": "val.json"})

# Use the text and label_id fields
def preprocess(example):
    return {"text": example["text"], "label": int(example["label_id"])}

dataset = dataset.map(preprocess)

model_name = "../LlamaModel/Llama-3.1-8B"  # Replace with your Llama model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)  # Set num_labels as needed
tokenizer.pad_token = tokenizer.eos_token
model.config.pad_token_id = tokenizer.pad_token_id

def tokenize_function(example):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=256)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

training_args = TrainingArguments(
    output_dir="./llama-finetuned",
    eval_strategy="epoch",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=1000,
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
)

trainer.train()