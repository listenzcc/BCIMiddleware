# %%
from BCIClient.dataCollector import DataStack

# %%
ds = DataStack('tmp_matrix')

help_message = dict(
    h='Help',
    q='Quit',
    r='Report all data',
    l='Fetch latest data',
    t='Start sending',
    k='Stop sending',
    s='Save all data'
)
# %%
while True:
    inp = input('>> ')
    if inp == '' or inp == 'h':
        for k in help_message:
            print(k, help_message[k])
        continue

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
