# FastToG: Wider, Deeper and Faster ToG
## Implement of FastToG
![illustration of FastToG](./main.png)
## How to run
1. For graph2text mode, please download: https://drive.google.com/file/d/1812Hy9eMHa_h7dQn70N6eQAmKR_x7WDH/view?usp=sharing
2. You can load the neo4j database of Wikidata from here: https://drive.google.com/file/d/1Vrdt86zqG2M1apaSAUciuqXx9BwQKd1g/view?usp=sharing
3. Given query and the subjectival entity:

python fasttog.py \ <br />
--query *What is the climate of the area where Pennsylvania Convention Center belong ?* \ <br />
--entity *Pennsylvania Convention Center* \ <br />
--llm_api *https://xxxx* \ <br />
--llm_api_key *xxxx* \ <br />
--llm_model *gpt-4o-mini* \ <br />
--graph2text_path *Path of Graph2Text Model* \ <br />
--kg_api *neo4j://xxxx* \ <br />
--kg_user *xxxx* \ <br />
--kg_pw *xxxx* \ <br />
--community_max_size *4*
