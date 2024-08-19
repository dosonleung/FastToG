# FastToG: Wider, Deeper and Faster ToG
1. for graph2text mode, please download: https://drive.google.com/file/d/1812Hy9eMHa_h7dQn70N6eQAmKR_x7WDH/view?usp=sharing
2. for you query and entity:
python3 fasttog.py \
	--query "What is the climate of the area where Pennsylvania Convention Center belong ?" \
	--entity "Pennsylvania Convention Center" \
	--llm_api "https://api.xiaoai.plus/v1" \
	--llm_api_key "sk-dzfmQUflukYgY0mH44EeAe26E0F240DbB6EaD38898Cc405c" \
	--llm_model "gpt-4o-mini" \
	--graph2text_path "/home/liangxj/workspace/FastToG/Model/finetune_t5" \
	--kg_api "neo4j://127.0.0.1:7687" \
	--kg_user "neo4j" \
	--kg_pw "neo4j123" \
	--community_max_size 4
