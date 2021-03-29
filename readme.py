# %%
import os


content = []


def read_all(folder):
    '''
    Read and dig into the [folder]
    find all the .md files,
    read them and put the contents into the 'content'
    '''
    # Escape if it is not a folder
    if not os.path.isdir(folder):
        return

    # For all children
    for e in os.listdir(folder):
        full = os.path.join(folder, e)

        # Dig into it
        if os.path.isdir(full):
            read_all(full)

        # Read it
        if e.endswith('.md'):
            content.append(open(full).read())


folders = [os.path.join(os.path.dirname(__file__), e)
           for e in os.listdir(os.path.dirname(__file__))]

for folder in folders:
    read_all(folder)

path = os.path.join(os.path.dirname(__file__), 'README_main.md')
readme = open(path).read()

readme = readme.replace('{{components}}',
                        '\n'.join([e for e in content]))


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'w') as f:
    f.write(readme)

# %%
