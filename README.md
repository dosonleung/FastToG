# FastToG: Wider, Deeper and Faster ToG
## Implement of FastToG
![illustration of FastToG](./main.png)
## How to run
1. For graph2text mode, please download: https://drive.google.com/file/d/1812Hy9eMHa_h7dQn70N6eQAmKR_x7WDH/view?usp=sharing
2. You can load the neo4j database of Wikidata from here: https://drive.google.com/file/d/1Vrdt86zqG2M1apaSAUciuqXx9BwQKd1g/view?usp=sharing
3. Given query and the subjectival entity:

python fasttog.py \ <br />
--query *"What is the climate of the area where Pennsylvania Convention Center belong ?"* \ <br />
--entity *"Pennsylvania Convention Center"* \ <br />
--base_path *.* \ <br />
--llm_api *https://xxxx* \ <br />
--llm_api_key *xxxx* \ <br />
--graph2text_path *Path_of_Graph2Text_Model* \ <br />
--kg_api *neo4j://xxxx* \ <br />
--kg_user *xxxx* \ <br />
--kg_pw *xxxx* \ <br />
--kg_graph_file_name *visulize* \ <br />
--community_max_size *4*

## Important Arguments
* **query** question you want to ask
* **entity** subjectival entity of you question. You should check the entity exist in the KG before running the script
* **base_path** path for the files of solution
* **graph2text_path** path for your download or pretained graph2text model. If none, T2T mode will be adopted.
* **kg_graph_file_name** image name of communities visulization (generated in the base_path)

## Output
===============================> answer: <br />
Status.OK humid continental climate <br />

