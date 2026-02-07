import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
import torchvision
import torchvision.transforms as transforms
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
from torchvision.models import resnet18


def setup():
    dist.init_process_group(backend="mpi")
    rank = dist.get_rank()

    if torch.cuda.is_available():
        # Map local rank to specific GPU
        local_rank = int(os.environ.get("FLUX_TASK_LOCAL_ID", 0))
        device = torch.device(f"cuda:{local_rank}")
        torch.cuda.set_device(device)
    else:
        device = torch.device("cpu")

    return rank, device


def train():
    rank, device = setup()
    world_size = dist.get_world_size()

    if rank == 0:
        print(f"Starting training on {world_size} nodes...")

    # 1. Data Prep (Standard CIFAR-10 transforms)
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )

    # Download dataset (only Rank 0 downloads, others wait)
    if rank == 0:
        torchvision.datasets.CIFAR10(root="./data", train=True, download=True)

    # Sync all ranks
    dist.barrier()

    trainset = torchvision.datasets.CIFAR10(
        root="./data", train=True, download=True, transform=transform
    )

    # DistributedSampler partitions the data so each rank gets 1/N of the images
    sampler = DistributedSampler(trainset, num_replicas=world_size, rank=rank)
    trainloader = torch.utils.data.DataLoader(
        trainset, batch_size=32, sampler=sampler, num_workers=2
    )

    # Model Prep...
    model = resnet18(num_classes=10).to(device)

    # Wrap model in DDP
    # For MPI backend on CPU, we use the model as is.
    # For GPU, DDP handles the internal gradient bucketing.
    model = DDP(model, device_ids=[device.index] if device.type == "cuda" else None)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001 * world_size, momentum=0.9)

    # Training Loop
    model.train()
    for epoch in range(2):  # Just 2 epochs for demonstration
        sampler.set_epoch(epoch)
        running_loss = 0.0

        for i, data in enumerate(trainloader, 0):
            inputs, labels = data[0].to(device), data[1].to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            if i % 100 == 99 and rank == 0:
                print(
                    f"[Epoch {epoch + 1}, Batch {i + 1}] Loss: {running_loss / 100:.3f}"
                )
                running_loss = 0.0

    if rank == 0:
        print("Finished Training.")

    dist.destroy_process_group()


if __name__ == "__main__":
    train()
