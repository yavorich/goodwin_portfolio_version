from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


channel_layer = get_channel_layer()


@async_to_sync
async def check_is_online(user):
    """
    Проверка на online по наличию подключения к сокету
    """
    group_name = "online"
    return await check_online_status(channel_layer, group_name)


async def check_online_status(channel_layer, group_name):
    """
    Проверка наличия канала в redis
    """
    connection = channel_layer.connection(channel_layer.consistent_hash(group_name))
    group_key = channel_layer._group_key(group_name)
    connection_count = await connection.zcard(group_key)
    return connection_count > 0
