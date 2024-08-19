# FastToG: Wider, Deeper and Faster ToG
## Implement of FastToG
![illustration of FastToG](https://github.com/dosonleung/FastToG/main.png)
## How to run
1. for graph2text mode, please download: https://drive.google.com/file/d/1812Hy9eMHa_h7dQn70N6eQAmKR_x7WDH/view?usp=sharing
2. for you query and entity:
python3 fasttog.py \
	--query "What is the climate of the area where Pennsylvania Convention Center belong ?" \
	--entity "Pennsylvania Convention Center" \
	--llm_api "https://xxxx" \
	--llm_api_key "xxxx" \
	--llm_model "gpt-4o-mini" \
	--graph2text_path "./finetune_t5" \
	--kg_api "neo4j://xxxx" \
	--kg_user "xxxx" \
	--kg_pw "xxxx" \
	--community_max_size 4
