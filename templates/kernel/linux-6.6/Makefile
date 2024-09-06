target_ko_name:=${TARGETKONAME}
obj-m:=  ${target_ko_name}.o

obj_list := $(subst &, ,$(OBJLIST))
$(info obj_list = $(obj_list))

${target_ko_name}-y:=$(obj_list)
$(info target_ko_name-y = ${target_ko_name}-y)

OHOS_BUILD_HOME:=${PROJECTDIR}

ifeq ($(DEVICENAME), rk3568)
KDIR:=${OHOS_BUILD_HOME}/out/kernel/OBJ/linux-6.6
else
KDIR:=${OHOS_BUILD_HOME}/out/KERNEL_OBJ/kernel/OBJ/linux-6.6
endif

CLANG_HOST_TOOLCHAIN := $(OHOS_BUILD_HOME)/prebuilts/clang/ohos/linux-x86_64/llvm/bin
CLANG_CC := $(CLANG_HOST_TOOLCHAIN)/clang

PAHOLE_TOOLCHAIN := $(OHOS_BUILD_HOME)/prebuilts/develop_tools/pahole/bin

KERNEL_ARCH=${DEVICEARCH}

KERNEL_CROSS_COMPILE:=
KERNEL_CROSS_COMPILE += CC="$(CLANG_CC)"

KERNEL_PREBUILT_MAKE := make LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
KERNEL_MAKE := \
    PATH="$(CLANG_HOST_TOOLCHAIN):$(PAHOLE_TOOLCHAIN):$$PATH" \
    $(KERNEL_PREBUILT_MAKE)

PWD:=$(shell pwd)

default:
	export KBUILD_MODPOST_WARN=1 && $(KERNEL_MAKE) -fstack-protector-all -C $(KDIR) ARCH=$(KERNEL_ARCH) $(KERNEL_CROSS_COMPILE) M=$(PWD) modules

clean:
	rm -rf .*.cmd *.o *.mod.c *.ko *.tmp_version *.order *symvers *Module.markers .*.o.d *.mod .thinlto-cache
