import re
from typing import Tuple, Set, Optional, List, Dict

community_triple_prune_best_prompt = """ 
Premise: (Van Andel Institute, research, Center for Epigenetics),(Van Andel Institute, education, 12th-grade inquiry-based science)
Question: Van Andel Institute was founded in part by what American businessman, who was best known as co-founder of the Amway Corporation?
A. (Van Andel Institute, affiliation, nonprofit organization)
B. (Van Andel Institute, country, United States of America)
C. (Van Andel Institute, donations, 12,393,285 United States dollar)
D. (Structural analysis of the dodecameric proteasome activator PafE in Mycobacterium tuberculosis, author, Lin Bai),(Lin Bai, employer, Van Andel Institute)
E. (Van Andel Institute, headquarters_location, Grand Rapids)
F. (Van Andel Institute, legal form, 501(c)(3) organization)
G. (Origins of cancer symposium report: beyond the tumor cell, author, Nikki M. Thellman), (Nikki M. Thellman, educated at, Van Andel Institute)
Your choice:
{C}
To slove the problem, we should dig out information about the founders of Van Andel Institute or Amway Corporation. Option C is most relevant because it can provide information about the financial contributions made to the Van Andel Institute, which may include donators in question. Then we can search whether founders were included in that donators.

Premise: (Royal Australian Air Force, mascot, kangaroo), (kangaroo, endemic to, Australian continent), (kangaroo, described by source, The New Student's Reference Work), (Australian continent, belong to, Australia), (Carmel Tebbutt, spouse, Anthony Albanese), (Anthony Albanese, position held, Prime Minister of Australia)
Question: The majority party now in the country whose symbol is kangaroo is Australian Labor Party, is it true of false?
A. (Carmel Tebbutt, writing language, English), (A recombinant calcitonin receptor independently stimulates 3',5'-cyclic adenosine monophosphate and Ca2+/inositol phosphate signaling pathways, language of work or name, English), (Eosinophilia Following Treatment of Patients with Schistosomiasis Mansoni and Bancroft's Filariasis, language of work or name, English)
B. (Anthony Albanese, work location, Canberra), (2017 Australian constitutional crisis, location, Canberra), (2017 Australian constitutional crisis, instance of, constitutional crisis)
C. (Australia, nominated by, Prime), (Mason, position held, Chief), (Mason, country of citizenship, Australia), (Knox, position held, Chief), (Knox, country of citizenship, Australia), (Mason, position held, Chief), (Knox, position held, Chief)
D. (station, officially opened by, Anthony), (station, designed by, Weston), (station, adjacent station, High)
E. (Tebbutt, sex or gender, female), (Streep, sex or gender, female), (Poletti, sex or gender, female), (Bates, sex or gender, female)
F. (Albanese, member of political party, Australian), (Carroll, member of political party, Australian), (Carroll, instance of, human), (Freelander, member of political party, Australian), (Freelander, instance of, human), (Freelander, member of political party, Australian)
Your choice:
{F} 
To solve the problem, we should firstly confirm that the country whose symbol is kangaroo. To my knowledge, this country is Australia, which is confirmed by the premise. Then, we should grab some information about politics of Australia. Comparing with others, option F is the most relevant one because it provides information about Prime Minister Antony's political party, the Australian Labor Party, and some of its members. 

Premise: (Pennsylvania Convention Center, located on street, Arch Street), (Wilson Brothers & Company, manufacturer of, Pennsylvania Convention Center), (Pennsylvania Convention Center, instance of, convention center)
Question: What is the climate in the area where Pennsylvania Convention Center belong to?
A. (Mauch Chunk, architect, Wilson Brothers), (Pennsylvania School for the Deaf, architect, Wilson Brothers)
B. (Calabar International Convention Centre, instance of, convention center)
C. (Winston Company, instance of, book publisher), (Winston Company, founded by, John Clark Winston), (Winston Science Fiction, publisher, John C)
D. (Old City, instance of, old town), (Old City, located in the administrative territorial entity, Philadelphia), (Old City, topic's main category, Category), (Philadelphia, category's main topic, Old City)
Your choice:
{D}
To solve the problem, we should dig out some geographical information about the area of Pennsylvania Convention Center. Comparing with others, option D is most revelant because it provides information such as the street to which the Pennsylvania Convention Center belongs - Arch Street (confirmed by the premise), the administrative district - Old City, etc. Among them, we also saw that Old City is located in Philadelphia. This will help us obtain climate information in the region.

Please retrieve the best choices (knowledge triples) that contribute to solve the following problem. Attention! You must output the best choices ID (A,B,C,...) in curly brackets like {X} and append the expanation "To solve the problem, ..." for your selection.
Premise: %s
Question: %s
%s
Your choice:
"""

community_triple_prune_topk_prompt = """ 
Premise: (Van Andel Institute, research, Center for Epigenetics),(Van Andel Institute, education, 12th-grade inquiry-based science)
Question: Van Andel Institute was founded in part by what American businessman, who was best known as co-founder of the Amway Corporation?
A. (Van Andel Institute, affiliation, nonprofit organization)
B. (Van Andel Institute, country, United States of America)
C. (Van Andel Institute, donations, 12,393,285 United States dollar)
D. (Structural analysis of the dodecameric proteasome activator PafE in Mycobacterium tuberculosis, author, Lin Bai),(Lin Bai, employer, Van Andel Institute)
E. (Van Andel Institute, headquarters_location, Grand Rapids)
F. (Van Andel Institute, legal form, 501(c)(3) organization)
G. (Origins of cancer symposium report: beyond the tumor cell, author, Nikki M. Thellman), (Nikki M. Thellman, educated at, Van Andel Institute)
Top 2 Best Choices:
{A,C}
To slove the problem, we should dig out information about the founders of Van Andel Institute or Amway Corporation. Option A is relevant because it can provide information about the individuals or organizations associated with the Van Andel Institute, we may get more information about the one who co-founded the VAI Corporation. Option C is the second relevant one because it can provide information about the financial contributions made to the Van Andel Institute, which may include donators in question. Then we can search whether founders were included in that donators.

Premise: (Pennsylvania Convention Center, located on street, Arch Street), (Wilson Brothers & Company, manufacturer of, Pennsylvania Convention Center), (Pennsylvania Convention Center, instance of, convention center)
Question: What is the climate in the area where Pennsylvania Convention Center belong to?
A. (Wilson Brothers & Company, manufacturer of, Pennsylvania Convention Center), (Mauch Chunk, architect, Wilson Brothers & Company), (Pennsylvania School for the Deaf, architect, Wilson Brothers & Company)
B. (Pennsylvania Convention Center, instance of, convention center), (Calabar International Convention Centre, instance of, convention center)
C. (Arch Street, located in the administrative territorial entity, Old City), (Old City, instance of, old town), (Old City, located in the administrative territorial entity, Philadelphia), (Old City, topic's main category, Category:Old City, Philadelphia), (Category:Old City, Philadelphia, category's main topic, Old City)
D. (John C. Winston Company, headquarters location, Arch Street), (John C. Winston Company, instance of, book publisher), (John C. Winston Company, founded by, John Clark Winston), (Winston Science Fiction, publisher, John C. Winston Company)
Top 3 Best Choices:
{A,C,D}
To solve the problem, we should dig out some geographical information about the area of Pennsylvania Convention Center. Option A provides information about the builder of Pennsylvania Convention Center. Although this information does not relate to the climate of the Pennsylvania Convention Center, perhaps we can infer information about the climate of the area from the location of the builder. Option C provides information such as the street to which the Pennsylvania Convention Center belongs - Arch Street, the administrative district - Old City, etc. Among them, we also saw that Old City is located in Philadelphia. This will help us obtain climate information in the region. Option D should also be included because provides information about the John C. Winston Company, the headquarters of Arch Street, the street on which the Pennsylvania Convention Center belongs. We can infer the climate of the area to which the Pennsylvania Convention Center belongs from the John C. Winston Company.

Premise: (Royal Australian Air Force, mascot, kangaroo), (kangaroo, endemic to, Australian continent), (kangaroo, described by source, The New Student's Reference Work), (Australian continent, belong to, Australia), (Carmel Tebbutt, spouse, Anthony Albanese), (Anthony Albanese, position held, Prime Minister of Australia)
Question: The majority party now in the country whose symbol is kangaroo is Australian Labor Party, is it true of false?
A. (Carmel Tebbutt, writing language, English), (A recombinant calcitonin receptor independently stimulates 3',5'-cyclic adenosine monophosphate and Ca2+/inositol phosphate signaling pathways, language of work or name, English), (Eosinophilia Following Treatment of Patients with Schistosomiasis Mansoni and Bancroft's Filariasis, language of work or name, English)
B. (Anthony Albanese, work location, Canberra), (2017 Australian constitutional crisis, location, Canberra), (2017 Australian constitutional crisis, instance of, constitutional crisis)
C. (Australia, nominated by, Prime), (Australia, country, Australia',), (Australia, country, Australia',), (Mason, position held, Chief), (Mason, country of citizenship, Australia',), (Knox, position held, Chief), (Knox, country of citizenship, Australia',), (Mason, position held, Chief), (Knox, position held, Chief)
D. (station, officially opened by, Anthony), (station, designed by, Weston), (station, adjacent station, High)
E. (Tebbutt, sex or gender, female), (Streep, sex or gender, female), (Poletti, sex or gender, female), (Bates, sex or gender, female)
F. (Albanese, member of political party, Australian), (Carroll, member of political party, Australian), (Carroll, instance of, human), (Freelander, member of political party, Australian), (Freelander, instance of, human), (Freelander, member of political party, Australian)
Top 3 Best Choices:
{B,C,F}
To solve the problem, we should firstly confirm that the country whose symbol is kangaroo. To my knowledge, this country is Australia, which is confirmed by the premise. Then, we should grab some information about politics of Australia. Option B is selected because it provides information about Australian Prime Minister Antony's workplace - Canberra. We can further look for answers from relevant information in Canberra.
Option C is also selected because it provides information about current politics in Australia. For example, Australia's Chief Justices Anthony Mason and Adrian Knox. We can infer the political parties to which politicians belong. The last one is option F which provides information about Prime Minister Antony's political party, the Australian Labor Party, and some of its members. 

Please retrieve the top %s best choices (knowledge triples) that contribute to solve the following problem. Attention! You must output the top %s choices ID in curly brackets and separated by comma like {A,B,C...} and append the expanation "To solve the problem, ..." for your selections.
Premise: %s
Question: %s
%s
Top %s Best Choices:
"""

community_text_prune_best_prompt = """ 
Premise: The Van Andel Institute focuses on research through its Center for Epigenetics and offers education in 12th-grade inquiry-based science.
Question: Van Andel Institute was founded in part by what American businessman, who was best known as co-founder of the Amway Corporation?
A. Van Andel Institute (VAI) is a 501(c)(3) nonprofit organization.
B. Van Andel Institute belongs to United States of America.
C. Van Andel Institute have donated 12,393,285 United States dollar.
D. Lin Bai, who is the author of "Structural Analysis of the Dodecameric Proteasome Activator PafE in Mycobacterium tuberculosis", is also an employee of VAI.
E. The headquarter location of Van Andel Institute is Grand Rapids.
F. Van Andel Institute is legal form, 501(c)(3) organization.
G. Nikki M. Thellman, the author of "Origins of Cancer Symposium Report: Beyond the Tumor Cell," was educated at VAI.
Choice:
{C} 
To slove the problem, we should dig out information about the founders of Van Andel Institute or Amway Corporation. Option C is most relevant because it can provide information about the financial contributions made to the Van Andel Institute, which may include donators in question. Then we can search whether founders were included in that donators.

Premise: The Pennsylvania Convention Center, which is located on Arch Street, is a convention center manufactured by Wilson Brothers & Company.
Question: What is the climate in the area where Pennsylvania Convention Center belong to?
A. The both architect of Mauch Chunk and Pennsylvania School for the Deaf are Wilson Brothers.
B. Calabar International Convention Centre is an instance of convention center.
C. The Winston Company is a book publisher founded by John Clark Winston. It has published the work "Winston Science Fiction," by an author known as John C.
D. Arch Street is one way through the Old City, which is an old town of Philadelphia.
Choice:
{D}
To solve the problem, we should dig out some geographical information about the area of Pennsylvania Convention Center. Comparing with others, option D is most revelant because it provides information such as the street to which the Pennsylvania Convention Center belongs - Arch Street (confirmed by the premise), the administrative district - Old City, etc. Among them, we also saw that Old City is located in Philadelphia. This will help us obtain climate information in the region.

Premise:  The Royal Australian Air Force is symbolized by the kangaroo, which is native to Australia. The kangaroo is featured in The New Student's Reference Work. Additionally, Carmel Tebbutt is married to Anthony Albanese, who has held the position of Prime Minister of Australia.
Question: The majority party now in the country whose symbol is kangaroo is Australian Labor Party, is it true of false?
A. Carmel Tebbutt and the mentioned scientific works like A recombinant calcitonin receptor independently stimulates 3',5'-cyclic adenosine monophosphate and Ca2+/inositol phosphate signaling pathways and Eosinophilia Following Treatment of Patients with Schistosomiasis Mansoni and Bancroft's Filariasis are all associated with the English language.
B. Anthony Albanese works in Canberra, the location associated with the 2017 Australian constitutional crisis, which is an instance of a constitutional crisis.
C. Mason and Knox both hold the position of Chief in Australia and are citizens of Australia. Additionally, Australia was nominated by Prime for a specific undisclosed context.
D. The station was officially opened by Anthony and designed by Weston. It is adjacent to the High station.
E. Tebbutt, Streep, Poletti, and Bates, are identified as female.
F. Albanese, Carroll and Freelander are both members of the Australian political party.
Choice:
{F}
To solve the problem, we should firstly confirm that the country whose symbol is kangaroo. To my knowledge, this country is Australia, which is confirmed by the premise. Then, we should grab some information about politics of Australia. Comparing with others, option F is the most relevant one because it provides information about Prime Minister Antony's political party, the Australian Labor Party, and some of its members. 

Please retrieve the best choices that contribute to solve the following problem. Attention! You must output the best choices ID (A,B,C,...) in curly brackets like {X} and append the expanation like "To solve the problem, ..." for your selection.
Premise: %s
Question: %s
%s
Your choice:
"""

community_text_prune_topk_prompt = """ 
Premise:  The Van Andel Institute focuses on research through its Center for Epigenetics and offers education in 12th-grade inquiry-based science.
Question: Van Andel Institute was founded in part by what American businessman, who was best known as co-founder of the Amway Corporation?
A. Van Andel Institute (VAI) is a 501(c)(3) nonprofit organization.
B. Van Andel Institute belongs to United States of America.
C. Van Andel Institute have donated 12,393,285 United States dollar.
D. Lin Bai, who is the author of "Structural Analysis of the Dodecameric Proteasome Activator PafE in Mycobacterium tuberculosis", is also an employee of VAI.
E. The headquarter location of Van Andel Institute is Grand Rapids.
F. Van Andel Institute is legal form, 501(c)(3) organization.
G. Nikki M. Thellman, the author of "Origins of Cancer Symposium Report: Beyond the Tumor Cell," was educated at VAI.
Top 2 Best Choices are:
{A,C} 
To slove the problem, we should dig out information about the founders of Van Andel Institute or Amway Corporation. Option A is relevant because it can provide information about the individuals or organizations associated with the Van Andel Institute, we may get more information about the one who co-founded the VAI Corporation. Option C is the second relevant one because it can provide information about the financial contributions made to the Van Andel Institute, which may include donators in question. Then we can search whether founders were included in that donators.

Premise: The Pennsylvania Convention Center, which is a convention center manufactured by Wilson Brothers & Company, is located on Arch Street. 
Question: What kind of clothing should I bring along if I head to the area around the Pennsylvania Convention Center in spring ?
A. The both architect of Mauch Chunk and Pennsylvania School for the Deaf are Wilson Brothers.
B. Calabar International Convention Centre is an instance of convention center.
C. The Winston Company is a book publisher founded by John Clark Winston. It has published the work "Winston Science Fiction," by an author known as John C.
D. Arch Street is one way through the Old City, which is an old town of Philadelphia.
Top 3 Best Choices are:
{A,C,D}
To solve the problem, we should dig out some geographical information about the area of Pennsylvania Convention Center. Option A provides information about the builder of Pennsylvania Convention Center. Although this information does not relate to the climate of the Pennsylvania Convention Center, perhaps we can infer information about the climate of the area from the location of the builder. Option C provides information such as the street to which the Pennsylvania Convention Center belongs - Arch Street, the administrative district - Old City, etc. Among them, we also saw that Old City is located in Philadelphia. This will help us obtain climate information in the region. Option D should also be included because provides information about the John C. Winston Company, the headquarters of Arch Street, the street on which the Pennsylvania Convention Center belongs. We can infer the climate of the area to which the Pennsylvania Convention Center belongs from the John C. Winston Company.

Premise: The Royal Australian Air Force is symbolized by the kangaroo, which is native to Australia. The kangaroo is featured in The New Student's Reference Work. Additionally, Carmel Tebbutt is married to Anthony Albanese, who has held the position of Prime Minister of Australia.
Question: The majority party now in the country whose symbol is kangaroo is Australian Labor Party, is it true of false?
A. Carmel Tebbutt and the mentioned scientific works like A recombinant calcitonin receptor independently stimulates 3',5'-cyclic adenosine monophosphate and Ca2+/inositol phosphate signaling pathways and Eosinophilia Following Treatment of Patients with Schistosomiasis Mansoni and Bancroft's Filariasis are all associated with the English language.
B. Anthony Albanese works in Canberra, the location associated with the 2017 Australian constitutional crisis, which is an instance of a constitutional crisis.
C. Mason and Knox both hold the position of Chief in Australia and are citizens of Australia. Additionally, Australia was nominated by Prime for a specific undisclosed context.
D. The station was officially opened by Anthony and designed by Weston. It is adjacent to the High station.
E. Tebbutt, Streep, Poletti, and Bates, are identified as female.
F. Albanese, Carroll and Freelander are both members of the Australian political party.
Top 3 Best Choices are:
{B,C,F}
To solve the problem, we should firstly confirm that the country whose symbol is kangaroo. To my knowledge, this country is Australia, which is confirmed by the premise. Then, we should grab some information about politics of Australia. Option B is selected because it provides information about Australian Prime Minister Antony's workplace - Canberra. We can further look for answers from relevant information in Canberra.
Option C is also selected because it provides information about current politics in Australia. For example, Australia's Chief Justices Anthony Mason and Adrian Knox. We can infer the political parties to which politicians belong. The last one is option F which provides information about Prime Minister Antony's political party, the Australian Labor Party, and some of its members. 

Please retrieve the top %s best choices that contribute to solve the following problem. Attention! You must output the top %s choices ID in curly brackets and separated by comma like {A,B,C...} and append the expanation like "To solve the problem, ..." for your selections.
Premise: %s
Question: %s
%s
Top %s Best Choices are:

"""

#options: dict like {'A':xxx, 'B':xxx, 'C':xxx}
#assert mode=='triple' or mode=='text'
def get_prune_prompt(premise:str, question:str, options:Dict[str, str], mode='triple', beam_size:int=3) -> str:
    option_str = ''
    assert question is not None
    assert mode=='triple' or mode=='text'
    assert len(options) >= 2 
    for i,k in enumerate(options):
        option_str += k + '. ' + options[k]
        if i < len(options)-1:
            option_str += '\n'
    if mode=='triple':
        if beam_size == 1:
            return community_triple_prune_best_prompt%(premise, question, option_str)
        else:
            return community_triple_prune_topk_prompt%(beam_size, beam_size, premise, question, option_str, beam_size)
    else:
        if beam_size == 1:
            return community_text_prune_best_prompt%(premise, question, option_str)
        else:
            return community_text_prune_topk_prompt%(beam_size, beam_size, premise, question, option_str, beam_size)

#answer format must follow the given examples
def get_prune_result(tags: Set[str], input_string: str) -> Tuple[int, List[str]]:
    match = re.search(r'\{(.+?)\}', input_string)
    if match:
        selection = match.group(1).split(',')
        selection = list(map(lambda x: x.strip(), selection))
        if set(selection).issubset(tags):
            return 1,selection  # Return the content inside the curly braces
        else:
            return 0,None 
    else:
        return 0,None

community_summary_prompt = """ 
Example 1:
Triples:
1. (Van Andel Institute, affiliation, nonprofit organization)
2. (Van Andel Institute, country, United States of America)
3. (Van Andel Institute, donations, 12,393,285 United States dollar)
4. (Structural analysis of the dodecameric proteasome activator PafE in Mycobacterium tuberculosis, author, Lin Bai)
5. (Lin Bai, employer, Van Andel Institute)
6. (Van Andel Institute, headquarters_location, Grand Rapids)
7. (Van Andel Institute, legal form, 501(c)(3) organization)
8. (Origins of cancer symposium report: beyond the tumor cell, author, Nikki M. Thellman)
9. (Nikki M. Thellman, educated at, Van Andel Institute)
Summary:
Van Andel Institute (VAI), which have donated 12,393,285 United States dollar, is a 501(c)(3) nonprofit biomedical research and science education organization in Grand Rapids, the United States of America. Lin Bai, who is the author of "Structural Analysis of the Dodecameric Proteasome Activator PafE in Mycobacterium tuberculosis", is also an employee of VAI. Nikki M. Thellman, the author of "Origins of Cancer Symposium Report: Beyond the Tumor Cell," was educated at VAI.

Example 2:
Triples:
1. (Pennsylvania Convention Center, located on street, Arch Street)
2. (Arch Street, located in the administrative territorial entity, Old City)
3. (Old City, instance of, old town)
4. (Old City, located in the administrative territorial entity, Philadelphia)
5. (Old City, topic's main category, Category)
6. (Philadelphia, category's main topic, Old City)
Summary:
Pennsylvania Convention Center is located on Arch Street. Arch Street is a one-way street through Old City, which is an old town in Philadelphia.

Example 3:
Triples:
1. (Anthony Albanese, work location, Canberra)
2. (Anthony Albanese, position held, Prime Minister of Australia)
3. (Anthony Albanese, member of political party, Australian Labor Party)
4. (Airport Line, officially opened by, Anthony)
5. (Airport Central railway station, officially opened by, Anthony)
6. (Carmel Tebbutt, spouse, Anthony Albanese)
Summary:
Anthony Albanese is the prime minister of Australia and a member of the Australian Labor Party, so he works in Canberra. The Airport Line and Airport Central railway station were officially opened by Prime Minister Anthony Albanese. In Anthony Albanese's family, Carmel Tebbutt is his spouse.

Given a community, which is a list of knowledge graph triples (entity, relation, entity), please summary the following community into text as short as possible.
Triples: 
%s
Your Summary:

"""

#triples: [('Charles Dolan, father, James L. Dolan'), ...]
def get_summary_prompt(triples:List[Tuple[str]]) -> str:
    triple_list = []
    for index,triple in enumerate(triples):
        triple_list.append(str(index+1) + '. ' + triple)
    triple_string = '\n'.join(triple_list)
    return community_summary_prompt%triple_string

#answer format must follow the given examples
def get_summary_result(input_string: str) -> str:
    if input_string is not None:
        return 1,input_string
    else:
        return 0,None

community_reasoning_triple_prompt = """
Given the context (knowledge triples) and a question Q, you are asked to answer the question in curly brackets like {Answer} if you can or {Unknown} if you can not. 
Tips for solution: 
First, please rewrite the question into different basic questions. 
Second, search the context for the information needed to answer these questions. 
Finally, organize all the information and your knowledge to answer.

context:
1. (Imperial Japanese Army, allegiance, Emperor of Japan)
2. (Yamaji Motoharu, allegiance, Emperor of Japan)
3. (Yamaji Motoharu, military rank, general)
Q: Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire ?
A: 
First, the question can be rewrote as: Viscount Yamaji Motoharu was a general of the early Imperial Japanese Army. Which empire did he belong to? 
Second, Based on the context, Viscount Yamaji Motoharu, who was a general in the early Imperial Japanese Army, belonged to the Empire of Japan.
Third, to my knowledge, Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army, which belonged to the Empire of Japan,  which also confirmed by the context.
To sum up, the answer is {Empire of Japan}.

context:
1. (Steve Bisciotti, country of citizenship, United States of America), (Steve Bisciotti, educated at, Severn School), (Steve Bisciotti, residence, Millersville), (Steve Bisciotti, sport, American football)
2. (Dallas Cowboys, instance of, National Football League), (New England Patriots, instance of, National Football League), (Kansas City Chiefs, instance of, National Football League), (Baltimore Ravens, instance of, National Football League)
3. ( Steve Bisciotti, sport, American football)
Q: Who is the coach of the team owned by the Steve Bisciotti?
A: 
First, the problem can be rewrote as: which team is owned by Steve Bisciotti ? who is the coach of that team ?
Second, context 1 provides geographical information about Millersville. Context 2 lists some football team of National Football League. Context 3 memtioned that Steve Bisciotti is American football player.
Third, context do not directly reveal the current coach of the team owned by Steve Bisciotti. To my knowledge, Steve Bisciotti is the owner of Baltimore Ravens, and the coach of Baltimore Ravens is John Harbaugh. 
To sum up, the answer is {John Harbaugh}.

context:
1. (Květa Peschke, citizen of, Czech)
2. (John Newcombe, date of birth, +1944-05-23T00:00:00Z)
3. (Květa Peschke, date of birth, +1975-07-09T00:00:00Z)
4. (John Newcombe, country of citizenship, Australia)
Q: John Newcombe is younger than Květa Peschke, is it true or false? 
A: 
First, the problem do not need to rewrote beacause it is clear. To solve the problem, we should compare the age or birthday about John Newcombe and Květa Peschke.
Second, context 2 mentioned that John Newcombe was born in 1944 and context 3 mentioned that Květa Peschke was born in 1975. 
Third, compare the above birthday, John Newcomb is not younger than Květa Peschke.
To sum up, the answer is {false}.

context:
1. (San Antonio Spurs, home venue, Alamodome), (San Antonio Spurs, home venue, AT&T Center), (San Antonio Spurs, home venue, Fort Worth Convention Center)
2. (AT&T Center, occupant, San Antonio Spurs)
3. (Fort Worth Convention Center, located in the administrative territorial entity, Texas), (Fort Worth Convention Center, occupant, San Antonio Spurs)
Q: At what stadium did Mychal George Thompson play home games with the San Antonio Spurs?
A: 
First, the question can be broken down into sub-questions: What team did Mychal George Thompson play for? What is the home venue of the San Antonio Spurs?
Second, context by context: Context 1 mentions that the San Antonio Spurs are occupants of the AT&T Center, which is their home venue. Context 2 incorrectly states that the San Antonio Spurs are the home venue of Alamodome and Fort Worth Convention Center; it should have said they used to play at these venues before moving to AT&T Center. Context 3 says the Fort Worth Convention Center is located in Texas and is associated with the San Antonio Spurs.
Finally, organizing the information and my knowledge:
The San Antonio Spurs currently play their home games at the AT&T Center. The historical venues include Alamodome and the Fort Worth Convention Center. If Mychal George Thompson played with the San Antonio Spurs, he could have played at one of these venues, depending on the period he was associated with the team.
Because the context does not specify when Mychal George Thompson played for the San Antonio Spurs or if he did, we cannot explicitly answer which stadium he played at. However, based on the common knowledge, he did not play for the Spurs.
To sum up, the answer is {Unknown}.

context:
1. (Pennsylvania Convention Center, located on street, Arch Street), (Wilson Brothers & Company, manufacturer of, Pennsylvania Convention Center), (Pennsylvania Convention Center, instance of, convention center).
2. (Wilson Brothers & Company, manufacturer of, Pennsylvania Convention Center); (Mauch Chunk, architect, Wilson Brothers & Company), (Pennsylvania School for the Deaf, architect, Wilson Brothers & Company)
3. (Arch Street, located in the administrative territorial entity, Old City); (Old City, instance of, old town), (Old City, located in the administrative territorial entity, Philadelphia), (Philadelphia, State of, Pennsylvania), (Pennsylvania, climate, humid subtropical climate)
4. (John C. Winston Company, headquarters location, Arch Street), (John C. Winston Company, instance of, book publisher), (John C. Winston Company, founded by, John Clark Winston), (Winston Science Fiction, publisher, John C. Winston Company)
Q: What is the climate in the area around the Pennsylvania Convention Center?
A: 
First, the question can be rewrote as: Where is Pennsylvania Convention Center? What is the climate there ?
Second, Context 1 mentions the location of the manufacturer of Pennsylvania Convention Center. Context 2 talk about some design and construction of Wilson Brothers & Company. Context 3 provides location information about the Pennsylvania Convention Center.
Third, the Pennsylvania Convention Center is located in Arch Street, Old City, Philadelphia. We can sure that Philadelphia is the city in the Pennsylvania. To my knowledge, the climate in State Pennsylvania is classified as a humid subtropical climate.
To sum up, the answer is {humid subtropical climate}.

context:
%s
Q: %s
A:
"""

community_reasoning_text_prompt = """
Given the context and a question Q, you are asked to answer the question in curly brackets like {Answer} if you can or {Unknown} if you can not. 
Tips for solution: 
First, please rewrite the question into different basic questions. 
Second, search the context for the information needed to answer these questions. 
Finally, organize all the information and your knowledge for the answer.

context:
1. The Imperial Japanese Army is allegiance to the Emperor of Japan.
2. Yamamaji Motoharu is the allegiance of the Emperor of Japan.
3. Yamada Motoharu is a general.
Q: Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire ?
A: 
First, the question can be rewrote as: Viscount Yamaji Motoharu was a general of the early Imperial Japanese Army. Which empire did he belong to? 
Second, Based on the context, Viscount Yamaji Motoharu, who was a general in the early Imperial Japanese Army, belonged to the Empire of Japan.
Third, to my knowledge, Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army, which belonged to the Empire of Japan,  which also confirmed by the context.
To sum up, the answer is {Empire of Japan}.

context:
1. Millersville is a locality situated within Anne Arundel County, which is in the Baltimore metropolitan area of Maryland.
2. Dallas Cowboys, New England Patriots, Kansas City Chiefs, Baltimore Ravens and Seattle Seahawks are instances of National Football League, which is a professional American football league consisting of 32 teams.
3. Steve Bisciotti is an American football player.
Q: Who is the coach of the team owned by the Steve Bisciotti?
A: 
First, the problem can be rewrote as: which team is owned by Steve Bisciotti ? who is the coach of that team ?
Second, context 1 provides geographical information about Millersville. Context 2 lists some football team of National Football League. Context 3 memtioned that Steve Bisciotti is American football player.
Third, context do not directly reveal the current coach of the team owned by Steve Bisciotti. To my knowledge, Steve Bisciotti is the owner of Baltimore Ravens, and the coach of Baltimore Ravens is John Harbaugh. 
To sum up, the answer is {John Harbaugh}.

context:
1. Květa Peschke is a citizen of Czech.
2. John Newcombe was born on +1944-05-23T00:00:00Z.
3. Květa Peschke was born on 07/09/1995 at 00:00Z.
4. John Newcombe is a citizen of Australia.
Q: John Newcombe is younger than Květa Peschke, is it true or false? 
A: 
First, the problem do not need to rewrote beacause it is clear. To solve the problem, we should compare the age or birthday about John Newcombe and Květa Peschke.
Second, context 2 mentioned that John Newcombe was born in 1944 and context 3 mentioned that Květa Peschke was born in 1975. 
Third, compare the above birthday, John Newcomb is not younger than Květa Peschke.
To sum up, the answer is {false}.

context:
1. San Antonio Spurs are occupants of the AT&T Center, which is also home vanue of AT&T Center.
2. San Antonio Spurs are home venue of Alamodome and Fort Worth Convention Center.
3. The Fort Worth Convention Center, who are occupant of San Antonio Spurs, is located in Texas.
Q: At what stadium did Mychal George Thompson play home games with the San Antonio Spurs?
A: 
First, the question can be broken down into sub-questions: What team did Mychal George Thompson play for? What is the home venue of the San Antonio Spurs?
Second, context by context: Context 1 mentions that the San Antonio Spurs are occupants of the AT&T Center, which is their home venue. Context 2 incorrectly states that the San Antonio Spurs are the home venue of Alamodome and Fort Worth Convention Center; it should have said they used to play at these venues before moving to AT&T Center. Context 3 says the Fort Worth Convention Center is located in Texas and is associated with the San Antonio Spurs.
Finally, organizing the information and my knowledge:
The San Antonio Spurs currently play their home games at the AT&T Center. The historical venues include Alamodome and the Fort Worth Convention Center. If Mychal George Thompson played with the San Antonio Spurs, he could have played at one of these venues, depending on the period he was associated with the team.
Because the context does not specify when Mychal George Thompson played for the San Antonio Spurs or if he did, we cannot explicitly answer which stadium he played at. However, based on the common knowledge, he did not play for the Spurs.
To sum up, the answer is {Unknown}.

context:
1. Wilson Brothers & Company manufactured the Pennsylvania Convention Center, which is located on Arch Street.
2. Wilson Brothers & Company is an architectural firm that was involved in the design and construction of several prominent structures. Some of their projects include the Pennsylvania Convention Center, Mauch Chunk, Pennsylvania School for the Deaf, and Wayne Junction. Wayne Junction serves as an adjacent station to Olney, and Fern Rock Transportation Center connects to Wayne Junction.
3. The Arch Street runs through Old City, an old town situated in Philadelphia. Additionally, Pennsylvania Convention Center can be found on Arch Street. Pennsylvania Academy of the Fine Arts is another institution located within Philadelphia.
4. John C. Winston Company, a book publisher founded by John Clark Winston and headquartered on Arch Street, was involved in publishing Winston Science Fiction. John Clark Winston, Juanita Breckenridge Bates, and Harriet Calista Clark McCabe are all citizens of the United States of America.
Q: What is the climate in the area around the Pennsylvania Convention Center?
A: 
First, the question can be rewrote as: Where is Pennsylvania Convention Center? What is the climate there ?
Second, Context 1 mentions the location of the manufacturer of Pennsylvania Convention Center. Context 2 talk about some design and construction of Wilson Brothers & Company. Context 3 provides location information about the Pennsylvania Convention Center.
Third, the Pennsylvania Convention Center is located in Arch Street, Old City, Philadelphia. We can sure that Philadelphia is the city in the Pennsylvania. To my knowledge, the climate in State Pennsylvania is classified as a humid subtropical climate.
To sum up, the answer is {humid subtropical climate}.

context:
%s
Q: %s
A:
"""

#clues: dict like {'A':xxx, 'B':xxx, 'C':xxx}
#assert mode=='triple' or mode=='text'
def get_reasoning_prompt(premise:str, question:str, clues:dict, mode='triple') -> str:
    assert question is not None
    assert mode == 'triple' or mode == 'text'
    assert len(clues) >= 1
    start,count = 0,0
    clue_str = ''
    if len(premise.strip()) > 0:
        clue_str = '1. ' + premise + '\n'
        start = 1
    for i,k in enumerate(clues):
        if len(clues[k].strip()) > 1:
            count += 1
            if i < len(clues)-1:
                clue_str += str(count+start) + '. ' + str(clues[k]) + '\n'
            else:
                clue_str += str(count+start) + '. ' + str(clues[k])
    assert count > 0
    if mode == 'triple':
        return community_reasoning_triple_prompt%(clue_str, question)
    else:
        return community_reasoning_text_prompt%(clue_str, question)

#unknown word set
UNK_WORD = set(['unknown','unk','unknow','unkown','none','unidentified','unclear','uncertain','not sure','not available','unavailable','unfortunately','unsure','however','answer','your answer'])
REJECT_WORD = set(['sorry','i am sorry','i\'m sorry','sorry','sorry,','sorry.','unable','can\''])

#answer format must follow the given examples
#0 unknown 1 ok -1 error
def get_reasoning_result(input_string: str) -> Tuple[int, Optional[str]]:
    #match = re.search(r"\{([^}]*)\}", input_string) 
    match = re.findall(r"\{([^{}]*)\}[^{}]*$", input_string)
    if match:
        answer = match[-1]
        if answer.lower().strip() in UNK_WORD:
            return 0,None
        else:
            return 1,answer
    else:
        if set(input_string.lower().split(' ')).intersection(REJECT_WORD):
            return 0,None
        else:
            return -1, None

direct_answer_prompt = """
Question: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
Answer: Washington, D.C.

Question: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
Answer: Bharoto Bhagyo Bidhata

Question: Who was the artist nominated for an award for You Drive Me Crazy?
Answer: Jason Allen Alexander

Question: What person born in Siegen influenced the work of Vincent Van Gogh?
Answer: Peter Paul Rubens

Question: What is the country close to Russia where Mikheil Saakashvii holds a government position?
Answer: Georgia

Question: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
Answer: Heroin

Please answer the following question directly. You just need to output the answer.
Question: %s
Answer: 
"""

def get_direct_answer_prompt(question:str) -> str:
    assert question is not None
    return direct_answer_prompt%question

def get_direct_answer_result(input_string:str) -> Tuple[int,str]:
    if input_string is not None:
        if input_string.lower().strip() in UNK_WORD:
            return 0,None
        if set(input_string.lower().split(' ')).intersection(REJECT_WORD):
            return 0,None
        return 1,input_string
    else:
        return 0,None

cot_answer_prompt = """
Question: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
Answer: First, the education institution has a sports team named George Washington Colonials men's basketball in is George Washington University , Second, George Washington University is in Washington D.C. The answer is {Washington, D.C.}.

Question: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
Answer: {Bharoto Bhagyo Bidhata} First, Bharoto Bhagyo Bidhata wrote Jana Gana Mana. Second, Bharoto Bhagyo Bidhata lists Pramatha Chaudhuri as an influence. The answer is {Bharoto Bhagyo Bidhata}.

Question: Who was the artist nominated for an award for You Drive Me Crazy?
Answer: First, the artist nominated for an award for You Drive Me Crazy is Britney Spears. The answer is {Jason Allen Alexander}.

Question: What person born in Siegen influenced the work of Vincent Van Gogh?
Answer: First, Peter Paul Rubens, Claude Monet and etc. influenced the work of Vincent Van Gogh. Second, Peter Paul Rubens born in Siegen. The answer is {Peter Paul Rubens}.

Question: What is the country close to Russia where Mikheil Saakashvii holds a government position?
Answer: First, China, Norway, Finland, Estonia and Georgia is close to Russia. Second, Mikheil Saakashvii holds a government position at Georgia. The answer is {Georgia}.

Question: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
Answer: {Heroin} First, Mitchell Lee Hedberg portrayed character Urethane Wheels Guy. Second, Mitchell Lee Hedberg overdose Heroin. The answer is {Heroin}.

Please solve the following question step by step. Note that you answer should be enclosed in curly brackets like {Answer}.  
Question: %s
Your Answer:
"""

def get_cot_prompt(question:str) -> str:
    assert question is not None
    return cot_answer_prompt%(question)

def get_cot_answer_result(input_string:str) -> Tuple[int,str]:
    match = re.search(r"\{([^}]*)\}", input_string)
    if match:
        answer = match.group(1)
        if answer.lower().strip() in UNK_WORD:
            return 0,None
        if set(answer.lower().split(' ')).intersection(REJECT_WORD):
            return 0,None
        return 1,answer
    return 0,None