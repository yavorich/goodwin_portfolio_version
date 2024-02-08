from asgiref.sync import sync_to_async


@sync_to_async
def get_sync_attr(__o, name):
    return getattr(__o, name)
