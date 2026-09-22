# sweet-pixelos-kernel

PixelOS (Android 17) kernel for Redmi Note 10 Pro / Pro Max (`sweet` / `sweetin`) built via GitHub Actions with in-tree KernelSU-Next, SuSFS, and NoMount.

## TL;DR

Grab the latest zip from [Releases](../../releases), flash in recovery (TWRP/OrangeFox), reboot. No wipe needed.

```bash
# Verify checksum if you care
sha256sum -c PixelOS-sweet-KernelSU-Next-SuSFS-NoMount-*.zip.sha256
```

Manager APK: [KernelSU-Next Releases](https://github.com/KernelSU-Next/KernelSU-Next/releases) (v3.2.0 recommended for legacy driver).

---

## Specs

- **Device**: Redmi Note 10 Pro / Pro Max (`sweet` / `sweetin`)
- **SoC**: Snapdragon 732G (`sm6150` / `sdmsteppe`)
- **Kernel**: Linux `4.14.357` ([`PixelOS-Devices/android_kernel_xiaomi_sm6150:seventeen`](https://github.com/PixelOS-Devices/android_kernel_xiaomi_sm6150/tree/seventeen))
- **Compiler**: ZyCromerZ Clang 17.0.0 + Greenforce bare-metal GCC (arm64/arm)
- **Root**: KernelSU-Next (`legacy-susfs`, kprobes hook)
- **Hiding**: SuSFS `v1.5.5` (`simonpunk/susfs4ksu:kernel-4.14`)
- **Module Engine**: NoMount (`maxsteeel/nomount`, `CONFIG_NOMOUNT=y`)
- **Packaging**: AnyKernel3 (`split_boot` / `flash_boot` — preserves stock OEM ramdisk & DTB)

---

## What's Patched

1. **KernelSU-Next**:
   - In-tree build under `drivers/kernelsu/`.
   - Dynamic kprobes hooking (`CONFIG_KSU_KPROBES_HOOK=y`).
   - `ktime_get_boottime_ts64` alignment for 4.14 timespec compat.
   - Neutralized `selinux_hide` write hijack to avoid Android 14+ Zygote specialization crash (`SIGABRT` on app launch).

2. **SuSFS 4.14**:
   - Core hooks in `fs/` (`dcache`, `namei`, `namespace`, `proc`).
   - Adapted `fs/proc/cmdline.c` and `fs/proc/task_mmu.c` for sweet's SKU command-line structure.
   - Mount isolation, kstat spoofing, path hiding, uname spoofing.

3. **NoMount**:
   - VFS-level directory lookup and redirection (`fs/nomount/`).
   - Zero bind mounts / overlayfs pollution in `/proc/mounts`.

4. **AnyKernel3**:
   - Uses `split_boot; flash_boot;` instead of `dump_boot`.
   - Never repacks first-stage init ramdisk to prevent SELinux context corruption on Android 17.
   - Leaves stock boot.img DTB untouched.

---

## Build

Dispatched manually via `workflow_dispatch` (no auto-commit triggers):

```bash
gh workflow run build.yml
```

Outputs flashable AK3 zip, generates SHA-256, tags release by date (`YYYY.MM.DD`), and pushes Telegram notification if bot secrets are set.

---

## Credits

- [PixelOS](https://github.com/PixelOS-AOSP)
- [KernelSU](https://github.com/tiann/KernelSU) & [KernelSU-Next](https://github.com/KernelSU-Next/KernelSU-Next)
- [simonpunk/susfs4ksu](https://gitlab.com/simonpunk/susfs4ksu)
- [maxsteeel/nomount](https://github.com/maxsteeel/nomount)
- [osm0sis/AnyKernel3](https://github.com/osm0sis/AnyKernel3)
- [ZyCromerZ Clang](https://github.com/ZyCromerZ/Clang)
