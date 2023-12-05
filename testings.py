a = ['asdasd', 'dasda', 'asdad ✅']
chat_ids = [item for item in a if item.endswith('✅')]
if chat_ids == []:
    print('si si')
else:
    print("not si")