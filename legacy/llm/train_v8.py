
import torch
import json
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

MODEL_ID   = "meta-llama/Llama-3.2-3B-Instruct"
OUTPUT_DIR = "/workspace/llm_project/output_v8"
DOMAIN_DATA_PATH = "/workspace/llm_project/data/battery_domain.json"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, quantization_config=bnb_config, device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

SYSTEM_PROMPT = "당신은 배터리 제조 공정 전문가입니다. 한국어로만 정확하게 답변하세요."

def format_text(instruction, output):
    return (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        f"{SYSTEM_PROMPT}<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n"
        f"{instruction}<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n"
        f"{output}<|eot_id|>"
    )

with open(DOMAIN_DATA_PATH) as f:
    domain_raw = json.load(f)

dataset = Dataset.from_list([
    {"text": format_text(x["instruction"], x["output"])}
    for x in domain_raw
])
split = dataset.train_test_split(test_size=0.2, seed=42)

print(f"학습: {len(split['train'])}개 / 검증: {len(split['test'])}개")

sft_config = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=10,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    learning_rate=2e-4,
    bf16=True,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=30,
    save_strategy="steps",
    save_steps=50,
    lr_scheduler_type="cosine",
    report_to="tensorboard",
)

trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    processing_class=tokenizer,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
print("학습 완료!")
