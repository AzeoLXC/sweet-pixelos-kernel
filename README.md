# PixelOS sweet Kernel with KernelSU-Next

Automated CI/CD builder for Xiaomi Redmi Note 10 Pro / Pro Max (`sweet` / `sweetin`) stock PixelOS kernel with in-tree KernelSU-Next integration.

---

## Technical Specifications

| Parameter | Specification |
|---|---|
| Target Devices | Xiaomi Redmi Note 10 Pro (`sweet`), Redmi Note 10 Pro Max (`sweetin`) |
| SoC / Platform | Qualcomm Snapdragon 732G / SM6150 (`sdmsteppe`) |
| Linux Baseline | 4.14.357 LTS (`openela-Alita`) |
| Upstream Baseline | [`SoloSaravanan/kernel_xiaomi_sm6150:17`](https://github.com/SoloSaravanan/kernel_xiaomi_sm6150/tree/17) (PixelOS 17 / Android 17) |
| C/C++ Compiler | ZyCromerZ Clang 17.0.0 (`clang-17.0.0-20230725`) |
| Assembler / Linker | LLVM Integrated Assembler (`LLVM=1 LLVM_IAS=1`, `ld.lld`) |
| Cross Compilers | Greenforce Bare-Metal GCC (`aarch64-elf-` & `arm-eabi-`) |
| Defconfig | `arch/arm64/configs/vendor/sweet_defconfig` |
| Root Solution | KernelSU-Next (branch `legacy`, tag `v3.2.0-legacy`) |
| Hook Implementation | Dynamic Kprobes (`CONFIG_KSU_KPROBES_HOOK=y`) |
| Output Artifact | AnyKernel3 flashable zip archive (`PixelOS-sweet-KernelSU-Next-*.zip`) |

---

## Architecture & Modifications

### 1. In-Tree Root Integration
* **Dynamic Hook Mode**: Configured with `CONFIG_KSU_KPROBES_HOOK=y`, `CONFIG_KPROBES=y`, and `CONFIG_KRETPROBES=y` for non-GKI 4.14 syscall interception.
* **4.14 Timespec Alignment**: Injected patch into `KernelSU-Next/kernel/sulog/event.c` substituting legacy `get_monotonic_boottime` with `ktime_get_boottime_ts64(&ts)` to prevent `struct timespec64 *` pointer mismatch under Clang `-Werror`.
* **Signature Bypass & Manager Binding**: Native manager APK signature verification enabled for official KernelSU and KernelSU-Next manager applications.

### 2. Toolchain & Build Optimizations
* **Clang 17 + LLD**: Compiled with full LLVM toolchain, ThinLTO link-time optimization, and openela patches.
* **Network Fault Tolerance**: Toolchains fetched via multi-threaded segmented chunking (`aria2c -s 16 -x 16`) inside ephemeral GitHub runners.

### 3. Pipeline Design
* **Job 1 (`check`)**: Queries upstream commit SHA from `SoloSaravanan` and generates ISO build timestamps.
* **Job 2 (`build`)**: Compiles `Image.gz` and device tree blobs (`dtb`), packages via AnyKernel3, generates SHA-256 checksums, and publishes a GitHub Release tagged with the build date (`YYYY.MM.DD`).
* **Job 3 (`notify`)**: Dispatches an HTML payload directly to Telegram group via Bot API with build metadata, SHA-256, and release download links.

---

## Flashing Instructions

### Prerequisites
* Unlocked bootloader.
* PixelOS (Android 17) installed.
* Custom recovery (TWRP or OrangeFox).

### Installation Steps
1. Download the latest `PixelOS-sweet-KernelSU-Next-*.zip` and matching `.sha256` from [Releases](../../releases).
2. (Optional) Verify checksum:
   ```bash
   sha256sum -c PixelOS-sweet-KernelSU-Next-*.zip.sha256
   ```
3. Reboot to custom recovery:
   ```bash
   adb reboot recovery
   ```
4. Flash the zip file directly (no cache or data wipe required).
5. Reboot to system.
6. Install [KernelSU-Next Manager APK](https://github.com/KernelSU-Next/KernelSU-Next/releases).

---

## Build Triggers

The workflow runs on-demand via `workflow_dispatch` without automatic commits or schedule polling:

1. Open **Actions** $\rightarrow$ **Build KernelSU Next PixelOS sweet**.
2. Click **Run workflow** (default branch: `legacy`).
3. Monitor build progress and receive the finished release link directly on Telegram.

---

## License

* Kernel source: [GNU General Public License v2.0 (GPL-2.0)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html).
* AnyKernel3 packaging: [osm0sis](https://github.com/osm0sis/AnyKernel3).
