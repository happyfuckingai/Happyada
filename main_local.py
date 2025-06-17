'''
Important: **Use headphones**. This script uses the system default audio
input and output, which often won't include echo cancellation. So to prevent
the model from interrupting itself it is important that you use headphones. 
'''

from ADA.ADA_Local import ADA
import asyncio

async def main():
    ada = ADA()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(ada.stt())
        input_message = tg.create_task(ada.input_message())
        tg.create_task(ada.send_prompt())
        tg.create_task(ada.tts())

        await input_message

if __name__ == "__main__":
    asyncio.run(main())