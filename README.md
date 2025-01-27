<div align="center">
    <h1>Fast Think-on-Graph: Wider, Deeper and Faster
      Reasoning of Large Language Model on Knowledge Graph</h1>
    <div>
        <a href='https://scholar.google.com/citations?user=BDYNU9MAAAAJ' target='_blank'>Xujian Liang</a><sup>1,2</sup>&emsp;
        <a href='https://scholar.google.com/citations?user=gtth-roAAAAJ' target='_blank'>Zhaoquan Gu</a><sup>2,3</sup>&emsp;
    </div>
    <div>
        <sup>1</sup>School of Cyberspace Security, Beijing University Of Posts And Telecommunications<br><sup>2</sup>Department of New Networks, Peng Cheng Laboratory<br><sup>3</sup>Harbin Institute of Technology (Shenzhen)
    </div>

</div>
<div align="center">

[![Paper](https://img.shields.io/badge/arXiv-PDF-b31b1b)](https://arxiv.org/abs/2501.14300)
[![Website](https://img.shields.io/badge/Poster-Link-blue)](https://github.com/dosonleung/FastToG/blob/main/FastToG_Poster.jpg)
[![License](https://img.shields.io/badge/License-Apache--2.0-929292)](https://www.apache.org/licenses/LICENSE-2.0)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=dosonleung/FastToG)

</div>
## --_Let's think community by community!_

## 📰News!
Our paper is accepted by AAAI 2025 👏👏👏. (surprising, it is accepted as ORAL!!!)

## 📜Poster
![illustration of FastToG](./FastToG_Poster.jpg)

## 🏇🏻How to run
1. For graph2text mode, please download the model(T5 sft): https://drive.google.com/file/d/1812Hy9eMHa_h7dQn70N6eQAmKR_x7WDH/view?usp=sharing
2. You can load the neo4j database of Wikidata from here: https://drive.google.com/file/d/1Vrdt86zqG2M1apaSAUciuqXx9BwQKd1g/view?usp=sharing
3. Given query and the subjectival entity:

```
python fasttog.py \
--query "What is the climate of the area where Pennsylvania Convention Center belong ?" \
--entity "Pennsylvania Convention Center" \
--base_path . \
--llm_api https://xxxx \
--llm_api_key xxxx \
--graph2text_path Path_of_Graph2Text_Model \
--kg_api neo4j://xxxx \
--kg_user xxxx \
--kg_pw xxxx \
--kg_graph_file_name visulize \
--community_max_size 4
```
## 🤔Arguments
* **query** question you want to ask
* **entity** subjectival entity of you question. You should check the entity exist in the KG before running the script
* **base_path** path for the files of solution
* **graph2text_path** path for your download or pretained graph2text model. If none, T2T mode will be adopted.
* **kg_graph_file_name** image name of communities visulization (generated in the base_path)

## 🧪Testcase
### Input
**query**: "What is the climate of the area where Pennsylvania Convention Center belong ?" <br />
**entity**: "Pennsylvania Convention Center" <br />

### Output
**status**: Status.OK <br />
**answer**:humid continental climate <br />

## 😎Visualize
The visulize.png in the path 'Pennsylvania\_Convention\_Center-1725603642' for solving this query is:
![visulize](./visulize.png)

## 🎩Claims
This project uses the Apache 2.0 protocol. The project assumes no legal responsibility for any of the model's output and will not be held liable for any damages that may result from the use of the resources and output.
