import os
import time
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
import torchvision
import torchvision.transforms as transforms
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
from torchvision.models import resnet18, resnet50


def get_args():
    parser = argparse.ArgumentParser(description="Distributed PyTorch Training (CIFAR-10)")

    # Optimization Hyperparameters
    parser.add_argument("--batch-size", type=int, default=32, 
                        help="Input batch size per replica (GPU/Process)")
    parser.add_argument("--lr", type=float, default=0.001, 
                        help="Base learning rate (will be scaled by world size)")
    parser.add_argument("--momentum", type=float, default=0.9, 
                        help="SGD momentum")
    parser.add_argument("--epochs", type=int, default=2, 
                        help="Number of epochs to train")
    
    # Architecture and Data
    parser.add_argument("--model", type=str, default="resnet18", choices=["resnet18", "resnet50"],
                        help="Model architecture to use")
    parser.add_argument("--num-workers", type=int, default=2, 
                        help="Number of data loading workers per process")
    parser.add_argument("--data-path", type=str, default="./data", 
                        help="Path to download/store CIFAR-10 dataset")

    # Distributed Configuration
    parser.add_argument("--backend", type=str, default="mpi", 
                        help="Distributed backend (mpi, nccl, gloo)")
    
    return parser.parse_args()


def setup(backend):
    dist.init_process_group(backend=backend)
    rank = dist.get_rank()

    if torch.cuda.is_available():
        # Flux usually sets LOCAL_ID; if not, we default to 0
        local_rank = int(os.environ.get("FLUX_TASK_LOCAL_ID", 0))
        device = torch.device(f"cuda:{local_rank}")
        torch.cuda.set_device(device)
    else:
        device = torch.device("cpu")

    return rank, device


def train():
    args = get_args()
    rank, device = setup(args.backend)
    world_size = dist.get_world_size()

    if rank == 0:
        print(f"--- Training Configuration ---")
        print(f"World Size:  {world_size}")
        print(f"Model:       {args.model}")
        print(f"Batch Size:  {args.batch_size} (Total: {args.batch_size * world_size})")
        print(f"Base LR:     {args.lr}")
        print(f"Scaled LR:   {args.lr * world_size}")
        print(f"-------------------------------")

    # 1. Data Prep
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )

    if rank == 0:
        torchvision.datasets.CIFAR10(root=args.data_path, train=True, download=True)
    dist.barrier()

    trainset = torchvision.datasets.CIFAR10(
        root=args.data_path, train=True, download=True, transform=transform
    )

    sampler = DistributedSampler(trainset, num_replicas=world_size, rank=rank)
    trainloader = torch.utils.data.DataLoader(
        trainset, 
        batch_size=args.batch_size, 
        sampler=sampler, 
        num_workers=args.num_workers
    )

    # 2. Model Prep
    if args.model == "resnet18":
        model = resnet18(num_classes=10).to(device)
    else:
        model = resnet50(num_classes=10).to(device)

    model = DDP(model, device_ids=[device.index] if device.type == "cuda" else None)

    criterion = nn.CrossEntropyLoss()
    # Common practice: Scale LR by world size
    optimizer = optim.SGD(model.parameters(), lr=args.lr * world_size, momentum=args.momentum)

    # 3. Training Loop
    model.train()
    start_time = time.time()
    
    for epoch in range(args.epochs):
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
                # Figure of Merit: Loss and Throughput
                elapsed = time.time() - start_time
                img_per_sec = (i * args.batch_size * world_size) / elapsed
                print(
                    f"[Epoch {epoch + 1}, Batch {i + 1}] Loss: {running_loss / 100:.3f} | Speed: {img_per_sec:.2f} img/s"
                )
                running_loss = 0.0

    if rank == 0:
        total_time = time.time() - start_time
        print(f"Finished Training. Total Time: {total_time:.2f}s")

    dist.destroy_process_group()


if __name__ == "__main__":
    train()
