'''Interactive UI for DataStack
'''
# %%
from TCPServer.dataCollector import DataStack

# %%
ds = DataStack('default_name')

# ds.start()

while True:
    inp = input('>> ')
    if inp == 'q':
        break

    if inp == 'r':
        ds.report()
        continue

    if inp == 'l':
        print(ds.latest().shape)
        continue

    if inp == 't':
        ds.start()
        continue

    if inp == 'k':
        ds.stop()
        continue

    if inp == 's':
        ds.save()
        continue

ds.close()
print('Done')
