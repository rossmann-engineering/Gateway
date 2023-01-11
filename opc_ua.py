import asyncio
import logging
import os

from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256, SecurityPolicyBasic256

class HelloClient:
    def __init__(self, endpoint):
        self.client = Client(endpoint)

    async def __aenter__(self):
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()


async def main(url, user, password, nodes, write=False):
    logging.getLogger('asyncio').setLevel(logging.ERROR)

    client = Client(url=url)
    #client.set_user(user)
    #client.set_password(password)

    packagedir = os.path.dirname(
        os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
    #directory = os.path.join(packagedir, 'certificates')  # Subdirectory
    #filename = os.path.join(directory, 'UaServerCpp@192.168.178.9 [3377E1809C827EAB87F9A5D22F2796BED0C436FB].der')
    #client.application_uri = "URI:urn:example.org:FreeOpcUa:python-opcua"
    #await client.load_client_certificate('my_cert.pem')
    #await client.load_private_key('my_private_key.pem')
    #await client.set_security_string("Basic256Sha256,SignAndEncrypt,my_cert.pem,my_private_key.pem")

    #await client.set_security(
    #    SecurityPolicyBasic256Sha256,
    #    certificate='my_cert.pem',
    #    private_key='my_private_key.pem',
        #server_certificate=filename
    #)




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
                if not write:
                    node['value'] = await child.get_value()
                else:
                    await child.set_value(node['value'])

        #await child.set_value(42)
        #print(await child.get_value())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    url = "opc.tcp://192.168.178.9:4840"
    asyncio.run(main(url, 'sr', 'Peachbarrow793!', ['ns=2;s=Application.GVL.iIntvar',
                                                    'ns=2;s=Application.GVL_1.iInt2']))