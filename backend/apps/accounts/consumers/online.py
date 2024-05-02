from channels.generic.websocket import AsyncJsonWebsocketConsumer


class OnlineConsumer(AsyncJsonWebsocketConsumer):
    online_group_name = "online"

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return await self.close(code=401)

        await self.channel_layer.group_add(self.online_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.online_group_name, self.channel_name
            )
