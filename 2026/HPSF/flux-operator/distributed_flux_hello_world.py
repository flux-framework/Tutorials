import os
import torch
import torch.distributed as dist


def run():
    # Don't set MASTER_ADDR or MASTER_PORT environment variables.
    # Let MPI handle the handshake entirely
    if not dist.is_initialized():
        dist.init_process_group(backend="mpi")

    rank = dist.get_rank()
    world_size = dist.get_world_size()
    print(f"Hello from Rank {rank}/{world_size}")

    # Dummy tensor for all-reduce
    tensor = torch.ones(1) * (rank + 1)
    dist.all_reduce(tensor)

    if rank == 0:
        print(f"Success! Result: {tensor.item()}")

    dist.destroy_process_group()


if __name__ == "__main__":
    run()
