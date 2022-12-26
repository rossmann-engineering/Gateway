import asyncio
import logging

from asyncua import Client


class HelloClient:
    def __init__(self, endpoint):
        self.client = Client(endpoint)

    async def __aenter__(self):
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()


async def main(url, user, password, nodes):
    client = Client(url=url)
    client.set_user(user)
    client.set_password(password)
    async with client:
        objects = client.nodes.objects
        client.get_server_node()
        print("Children of root are: %r", await client.nodes.objects.get_children())
        #child1 = await client.nodes.objects.get_child(['2:Application'])
        #print("Children of root are: %r", await child1.nodes.objects.get_children())
        for node in nodes:
            if type(node) is str:
                child = client.get_node(node)
                print(await child.get_value())
            else:
                child = client.get_node(node['address'])
                node['value'] = await child.get_value()

        #await child.set_value(42)
        #print(await child.get_value())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    url = "opc.tcp://192.168.178.9:4840"
    asyncio.run(main(url, 'sr', 'Peachbarrow793!', ['ns=2;s=Application.GVL.iIntvar',
                                                    'ns=2;s=Application.GVL_1.iInt2']))