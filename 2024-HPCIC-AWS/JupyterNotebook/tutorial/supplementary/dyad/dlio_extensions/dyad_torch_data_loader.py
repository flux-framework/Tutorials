"""
   Copyright (c) 2022, UChicago Argonne, LLC
   All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from time import time
import math
import pickle
import torch
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler

from dlio_benchmark.common.constants import MODULE_DATA_LOADER
from dlio_benchmark.common.enumerations import Shuffle, DatasetType, DataLoaderType
from dlio_benchmark.data_loader.base_data_loader import BaseDataLoader
from dlio_benchmark.reader.reader_factory import ReaderFactory
from dlio_benchmark.utils.utility import utcnow, DLIOMPI
from dlio_benchmark.utils.config import ConfigArguments

from pydyad import Dyad, dyad_open
from pydyad.bindings import DTLMode, DTLCommMode
import numpy as np
import flux
import os



class DYADTorchDataset(Dataset):
    """
    Currently, we only support loading one sample per file
    TODO: support multiple samples per file
    """
    def __init__(self, format_type, dataset_type, epoch, num_samples, num_workers, batch_size):
        self.format_type = format_type
        self.dataset_type = dataset_type
        self.epoch_number = epoch
        self.num_samples = num_samples
        self.reader = None
        self.num_images_read = 0
        self.batch_size = batch_size
        args = ConfigArguments.get_instance()
        self.serial_args = pickle.dumps(args)
        if num_workers == 0:
            self.worker_init(-1)
        self.broker_per_node = 1

    def worker_init(self, worker_id):
        # Configure PyTorch components
        pickle.loads(self.serial_args)
        self._args = ConfigArguments.get_instance()
        self._args.configure_dlio_logging(is_child=True)
        self.reader = ReaderFactory.get_reader(type=self.format_type,
                                               dataset_type=self.dataset_type,
                                               thread_index=worker_id,
                                               epoch_number=self.epoch_number)
        # Start initializing DYAD
        # Create Dyad object to interact with DYAD's C internals
        self.dyad_io = Dyad()
        # Create a handle to Flux and get the rank of the broker that this process is running on
        self.f = flux.Flux()
        self.broker_rank = self.f.get_rank()
        # Obtain DYAD's managed directory from the DYAD_PATH environment variable
        self.dyad_managed_directory = os.getenv("DYAD_PATH", "")
        # Get the DTL mode (UCX or FLUX_RPC) from the DYAD_DTL_MODE environment variable
        dtl_str = os.getenv("DYAD_DTL_MODE", "FLUX_RPC")
        mode = DTLMode.DYAD_DTL_FLUX_RPC
        if dtl_str == "UCX":
            mode = DTLMode.DYAD_DTL_UCX
        # Initialize DYAD
        self.dyad_io.init(debug=self._args.debug, check=False, shared_storage=False, reinit=False,
                          async_publish=True, fsync_write=False, key_depth=3,
                          service_mux=self.broker_per_node,
                          key_bins=1024, kvs_namespace=os.getenv("DYAD_KVS_NAMESPACE"),
                          prod_managed_path=self.dyad_managed_directory, cons_managed_path=self.dyad_managed_directory,
                          dtl_mode=mode, dtl_comm_mode=DTLCommMode.DYAD_COMM_RECV)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, image_idx):
        # For the requested sample (indicated by image_idx), determine the file
        # containing the sample and the index of the sample within that file
        self.num_images_read += 1
        step = int(math.ceil(self.num_images_read / self.batch_size))
        filename, sample_index = self._args.global_index_map[image_idx]
        is_present = False
        file_obj = None
        base_fname = filename
        # Use DYAD's `get_metadata` function to check if the file has already been cached
        # into DYAD
        if self.dyad_managed_directory != "":
            base_fname = os.path.join(self.dyad_managed_directory, os.path.basename(filename))
            file_obj = self.dyad_io.get_metadata(fname=base_fname, should_wait=False, raw=True)
            is_present = True
        # If the file has already been cached in DYAD, use `dyad_open` to open the file.
        # Then, pass the Python File object returned from `dyad_open` to NumPy to read data.
        if file_obj:
            access_mode = "remote"
            file_node_index = int(file_obj.contents.owner_rank*1.0 / self.broker_per_node)
            with dyad_open(base_fname, "rb", dyad_ctx=self.dyad_io, metadata_wrapper=file_obj) as f:
                try:
                    data = np.load(f, allow_pickle=True)["x"]
                except:
                    data = self._args.resized_image
            self.dyad_io.free_metadata(file_obj)
        # If the file has not been cached in DYAD, first read the file using a DLIO reader.
        # Then, write the data into the DYAD managed directory using `dyad_open`.
        else:
            data = self.reader.read_index(image_idx, step)
            if is_present:
                with dyad_open(base_fname, "wb", dyad_ctx=self.dyad_io) as f:
                    np.savez(f, x=data)

        return data

class DyadTorchDataLoader(BaseDataLoader):
    def __init__(self, format_type, dataset_type, epoch_number):
        super().__init__(format_type, dataset_type, epoch_number, DataLoaderType.PYTORCH)

    def read(self):
        do_shuffle = True if self._args.sample_shuffle != Shuffle.OFF else False
        dataset = DYADTorchDataset(self.format_type, self.dataset_type, self.epoch_number, self.num_samples, self._args.read_threads, self.batch_size)
        if do_shuffle:
            sampler = RandomSampler(dataset)
        else:
            sampler = SequentialSampler(dataset)
        if self._args.read_threads >= 1:
            prefetch_factor = math.ceil(self._args.prefetch_size / self._args.read_threads)
        else:
            prefetch_factor = self._args.prefetch_size
        if prefetch_factor <= 0:
            prefetch_factor = 2
            if self._args.my_rank == 0:
                logging.debug(f"{utcnow()} Setup dataloader with {self._args.read_threads} workers {torch.__version__}")
        if self._args.read_threads==0:
            kwargs={}
        else:
            kwargs={'multiprocessing_context':self._args.multiprocessing_context,
                    'prefetch_factor': prefetch_factor}
            if torch.__version__ != '1.3.1':
                kwargs['persistent_workers'] = True
        if torch.__version__ == '1.3.1':
            if 'prefetch_factor' in kwargs:
                del kwargs['prefetch_factor']
            self._dataset = DataLoader(dataset,
                                       batch_size=self.batch_size,
                                       sampler=sampler,
                                       num_workers=self._args.read_threads,
                                       pin_memory=True,
                                       drop_last=True,
                                       worker_init_fn=dataset.worker_init,
                                       **kwargs)
        else:
            self._dataset = DataLoader(dataset,
                                       batch_size=self.batch_size,
                                       sampler=sampler,
                                       num_workers=self._args.read_threads,
                                       pin_memory=True,
                                       drop_last=True,
                                       worker_init_fn=dataset.worker_init,
                                       **kwargs)  # 2 is the default value

        # self._dataset.sampler.set_epoch(epoch_number)

    def next(self):
        super().next()
        total = self._args.training_steps if self.dataset_type is DatasetType.TRAIN else self._args.eval_steps
        for batch in self._dataset:
            yield batch

    def finalize(self):
        pass
