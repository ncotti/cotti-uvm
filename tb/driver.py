from pyuvm import *
from common.tinyalu_ref import *
from bfm import *
from common.help import *


class Driver(uvm_driver):
    def start_of_simulation_phase(self):
        self.bfm = config_db_get("bfm")

    async def run_phase(self):
        await self.bfm.reset()
        self.bfm.start()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd)
            self.seq_item_port.item_done()