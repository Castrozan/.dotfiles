# AI Search — SoL-Refiner for MiniMax H3

Capture: `ReadItLater Inbox/Tweet from AI Search (2026-09-30 19-42-43).md`
Origin: https://x.com/aisearchio/status/2105403941903319360
Resolved project: https://github.com/NVlabs/Sana/tree/sol-engine/models/sol-refiner
Verdict: **drop**

## The origin as resolved

Read through the twitter skill with `twikit-cli tweet 2105403941903319360` and
`twikit-cli thread 2105403941903319360`, not through a topic search. It is a single post by AI Search
(@aisearchio), published 2026-09-30 21:06:30 UTC, with no self-thread. At read time it had 230 likes, 16
reposts, one reply and 8610 views. The text says, `Turn Minimax H3 generations into 2K/4K in just one step`.
Its first shortened link resolves to NVIDIA Research's `NVlabs/Sana` repository, branch `sol-engine`, at
`models/sol-refiner/`; the other shortened link is the post's own media.

The project's own material narrows the post's claim. The general SoL-Refiner work studies refinement up to
4K, but its MiniMax-H3 extension uses an LTX-2.5 refiner and publishes 1080p defaults. The H3 project-page
deployment is a five-second 1344×768 video on GB200 GPUs, while the released H3 README says the code was
tested on an H100 with 80 GB of VRAM. The H3 path is therefore not a demonstrated one-step 2K/4K workflow
for this machine.

## What it actually is

SoL-Refiner is a second-stage diffusion pipeline, not an upscaling filter and not a MiniMax H3 generator.
It takes an already-generated H3 MP4 plus its prompt, upsamples the latent representation, then performs one
target-resolution denoising step with an LTX-2.5-derived model before decoding a new MP4. The release pins a
Diffusers commit, requires PyTorch 2.9.1 or newer and a CUDA-matched NATTEN wheel, downloads a separate model
from Hugging Face, and requires an NVIDIA CUDA GPU. Its CLI uses CPU offload and decoder tiling, truncates
inputs to `8k + 1` frames, and drops the source audio.

"One step" describes one Transformer denoising step. It does not mean the whole operation is a lightweight
one-pass resize: video loading, text encoding, latent upsampling, diffusion decoding and MP4 encoding remain
around that step.

## What it touches here

Nothing in the current repository. There is no MiniMax H3 generator, video-generation service, or
post-generation refinement module to extend or replace. Adopting this would create a new standalone CUDA and
Python workload rather than improve an existing path.

The nearest machine boundary is chise's NVIDIA setup:

- `machine-configuration/machines/chise/system/configs/nvidia-policy.md:3` identifies the dGPU as an RTX
  3050 Ti.
- `machine-configuration/machines/chise/system/configs/nvidia.nix:22-62` owns the pinned NVIDIA driver and
  exposes `cudatoolkit`.
- `machine-configuration/media/arr-stack/stack/README.md:250-256` documents the existing use of that GPU:
  Jellyfin transcoding, not generative-video inference.

The live host reports 4096 MiB of VRAM. That is one twentieth of the H100 80 GB configuration on which the
released H3 refiner was tested. Packaging the Python dependencies would not bridge that hardware gap, and
the pinned 550.135 driver is also older than the CUDA 12.6/PyTorch combination named by the upstream test
environment. This capture therefore replaces nothing, deletes nothing, and unblocks nothing here.

## Reasoning

**Drop**, rather than adopt or trial. The strongest practical disproof is the upstream execution contract:
the only released H3 recipe is tested on an 80 GB H100, while the only CUDA host here has 4 GB. A trial would
first download large model weights and construct an incompatible Python/CUDA/NATTEN environment, then fail
before it could answer the quality question. Building a Nix module or container around it would make that
failure reproducible, not useful.

It is also not a learn. There is no specific technique this setup is ready to practise: the interesting
idea is embodied in a pretrained high-resolution video model that the host cannot run, not in a small
algorithm that transfers to an existing module.

It is not a reference either. The saved claim is materially broader than the released H3 evidence, and no
current project, skill or service here consumes H3 videos. Keeping a fast-moving model announcement in the
vault without a usable path would preserve a stale product pointer rather than durable knowledge. Revisit
SoL-Refiner from its upstream repository if a high-memory CUDA execution target and an actual H3 workflow
arrive; until both exist, this capture has no work left in it.

## Drafted vault entry

None. A drop files nothing.
