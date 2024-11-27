import csv
import sys
input_file = 'issues_bugs.csv'

lines = []

with open('data/' + input_file, 'r',  encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=';')
    rows = list(reader)        # Convert to list of rows
    
    for row in rows:
        line = ''
        for cell in row:
            line += cell + ';'
        lines.append(line)

# skip first line
lines = lines[1:]

import ollama

yes_count = 0
no_count = 0

model = 'mistral:instruct'
for line in lines:

    print('-------------------------------------------------------------------------------------------------------')
    

    question = f"issue:\n {line}\n \n Is this jira issues describe UI issue that can be potentialy backend issue? Use reasoning and chain of thoughts."
    
    print(question)
    response = ollama.chat(
        model=model,
        messages=[
            {'role': 'user', 'content': question}
        ]
    )
    #print(response['message']['content'])
    res_text = response['message']['content']

    question = res_text + "\n Is this describing rather backend issue than frontend issue? Start with Yes, if you think so."
    response = ollama.chat(
        model=model,
        messages=[
            {'role': 'user', 'content': question}
        ]
    )
    print(question)
    print('****************************************************************')
    res = response['message']['content']
    print(res)
    if res.startswith(' Yes') or res.startswith('Yes'):
        yes_count += 1
    else:
        no_count += 1

    print(f'Yes: {yes_count}, No: {no_count}')
    print('\n')
    print('\n')
    print('\n')
    print('\n')
    print('\n')
    print('\n')

    sys.stdout.flush()
    print('Appending results to file')
    with open('data/' + 'backend_issues.txt', 'a',  encoding='utf-8') as file:
        file.write('*'*20)
        file.write(line)
        file.write('\n')
        file.write('\n')
        file.write('\n')
    sys.stdout.flush()
    print('Results appended to file')
    #flush
    sys.stdout.flush()
    