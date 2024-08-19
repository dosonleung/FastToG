import torch
from transformers import T5Tokenizer,T5ForConditionalGeneration

TASK_PREFIX = 'triple to text: '
#model_path = "/home/liangxj/workspace/FastToG/Model/finetune_t5"

class graph2text_client:
    def __init__(self, model_path, max_length:int=128):
        self.tokenizer = T5Tokenizer.from_pretrained(model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = model.to(self.device)
        self.max_length = max_length

    def generate(self, triples:str, max_length=None) -> str:
        if len(triples) == 0:
            return ''
        inputs = self.tokenizer(TASK_PREFIX + triples, return_tensors="pt", padding=True).to(self.device)
        outputs = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length = max_length if max_length is not None else self.max_length,
            do_sample=False  # disable sampling to test if batching affects output
        ).cpu()
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[-1]