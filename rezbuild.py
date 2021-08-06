import os
import os.path
import sys
import shutil
import subprocess
import logging


logger = logging.getLogger(__name__)


def build(source_path, build_path, install_path, targets):
    def _deliver(src, dst, symlink=False):
        if not symlink:
            if os.path.isdir(src):
                basename = os.path.basename(src)
                dst = os.path.join(dst, basename)
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)
        else:
            basename = os.path.basename(src)
            dst = os.path.join(dst, basename)
            if sys.platform.startswith("win"):
                if os.path.isdir(src):
                    subprocess.call(["mklink", "/j", dst, src], shell=True)
                else:
                    subprocess.call(["mklink", dst, src], shell=True)
            else:
                os.symlink(dst, src)

    def _install():
        # check if argument "--symlink" presents
        symlink = False
        if int(os.environ["__PARSE_ARG_SYMLINK"]):
            symlink = True

        src = source_path

        logger.info("Src:{}".format(src))
        logger.info("Dst:{}".format(install_path))
        for name in os.listdir(src):
            # skipping some hidden files(e.g. .git)
            if name.startswith(".") or name == "build":
                continue

            file_path = os.path.abspath(os.path.join(src, name))
            _deliver(file_path, install_path, symlink)

        # package.py is to be copied to install path automatically by rez build system
        # _deliver(os.path.join(source_path, 'package.py'), install_path, symlink)

        # manage necessary files starts with '.'
        whitelist = []
        for f in whitelist:
            file_ = os.path.join(source_path, f)
            if os.path.isfile(file_):
                _deliver(file_, install_path, symlink)

    if "install" in (targets or []):
        _install()


# Below section is necessary for rez custom build system - custom.py,
# which executes build_command ("python {root}/rezbuild.py {install}") defined in package.py
if __name__ == "__main__":
    build(
        source_path=os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path=os.environ["REZ_BUILD_PATH"],
        install_path=os.environ["REZ_BUILD_INSTALL_PATH"],
        targets=sys.argv[1:],
    )
