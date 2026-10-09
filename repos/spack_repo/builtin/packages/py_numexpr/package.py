# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyNumexpr(PythonPackage):
    """Fast numerical expression evaluator for NumPy"""

    homepage = "https://github.com/pydata/numexpr"
    pypi = "numexpr/numexpr-2.14.1.tar.gz"

    license("MIT", checked_by="lgarrison")

    version("2.14.2", sha256="e7144e83ea9e581f2273e0304f15836736c4e470e2bd2e378ce617662a1ca278")
    version("2.14.1", sha256="4be00b1086c7b7a5c32e31558122b7b80243fe098579b170967da83f3152b48b")
    version("2.10.2", sha256="7e61a8aa4dacb15787b31c31bd7edf90c026d5e6dbe727844c238726e8464592")
    version("2.9.0", sha256="4df4163fcab20030137e8f2aa23e88e1e42e6fe702387cfd95d7675e1d84645e")
    version("2.8.8", sha256="10b377c6ec6d9c01349d00e16dd82e6a6f4439c8c2b1945e490df1436c1825f5")
    version("2.8.4", sha256="0e21addd25db5f62d60d97e4380339d9c1fb2de72c88b070c279776ee6455d10")
    version("2.8.3", sha256="389ceefca74eff30ec3fd03fc4c3b7ab3df8f22d1f235117a392ce702ed208c0")
    version("2.7.3", sha256="00d6b1518605afe0ed10417e0ff07123e5d531c02496c6eed7dd4b9923238e1e")
    version("2.7.2", sha256="7d1b3790103221feda07f4a93a4fa5c6654f46865197a677ca6f27eb5cb4e5ef")
    version("2.7.0", sha256="1923f038b90cc69635871968ed742be7775c879451c612f173c2547c823c9561")
    version("2.6.9", sha256="d57267bbdf10906f5ed7841b3484bec4af0494102b50e89ba316924cc7a7fd46")
    version("2.6.5", sha256="fe78a78e002806e87e012b6105f3b3d52d47fc7a72bafb56341fcec7ce02cfd7")
    version("2.6.1", sha256="e92c83d066fa8da63864d69b5f218287cc31437ae844db77390f2183123aab22")
    version("2.5", sha256="4ca111a9a27c9513c2e2f5b70c0a84ea69081d7d8e4512d4c3f26a485292de0d")
    version("2.4.6", sha256="2681faf55a3f19ba4424cc3d6f0a10610ebd49f029f8453f0ba64dd5c0fe4e0f")

    with default_args(type="build"):
        depends_on("c")
        depends_on("cxx")

        depends_on("py-setuptools@77:", when="@2.12:")
        depends_on("py-setuptools")

        depends_on("py-numpy@2:", when="@2.10.2:")

    with default_args(type=("build", "run")):
        depends_on("python@3.10:", when="@2.11:")
        depends_on("python@3.9:", when="@2.8.7:")
        depends_on("python@3.7:", when="@2.8.3:")

        depends_on("py-numpy@1.23:", when="@2.10.2:")
        depends_on("py-numpy@1.13.3:1.25", when="@2.8.3:2.9")
        # https://github.com/pydata/numexpr/issues/397
        depends_on("py-numpy@1.7:1.22", when="@:2.7")
        # https://github.com/pydata/numexpr/pull/478
        depends_on("py-numpy@:1", when="@:2.9")

        # Historical dependencies
        depends_on("py-packaging", when="@2.8.3")

    @when("%oneapi")
    def patch(self):
        self._patch_intel()

    @when("%intel")
    def patch(self):
        self._patch_intel()

    def _patch_intel(self):
        # Intel oneAPI math.h clashes with numexpr in two ways:
        #
        # 1. numexpr_config.hpp redefines signbitf/isfinited/isnand/isinfd as
        #    inline bool, but Intel math.h already declared them returning int.
        #    C++ rejects overloading on return type alone.
        #
        # 2. functions.hpp feeds raw signbit (int) into FuncBDPtr (bool(*)(double))
        #    and signbitf (int on Intel) into FuncBFPtr (bool(*)(float)).
        #    Intel strict mode rejects the implicit int->bool pointer conversion.
        #
        # Fix: guard the conflicting definitions behind a non-Intel preprocessor
        # check, add ne_* bool wrappers that work on all compilers, and update
        # functions.hpp to use the ne_* names in the function-pointer tables.
        #
        # Use raw bytes I/O to handle CRLF line endings in the tarball.
        # All bytes.replace() calls are no-ops on versions that lack the target
        # string, so this is safe across the full version range.

        # --- patch numexpr/numexpr_config.hpp ---
        config = "numexpr/numexpr_config.hpp"
        with open(config, "rb") as f:
            content = f.read()
        content = content.replace(b"\r\n", b"\n")

        # signbitf: guard the existing definition (Intel math.h declares it int).
        content = content.replace(
            b"inline bool signbitf(float x) { return signbit((double)x); }",
            b"#if !defined(__INTEL_COMPILER) && !defined(__INTEL_LLVM_COMPILER)\n"
            b"inline bool signbitf(float x) { return signbit((double)x); }\n"
            b"#endif",
        )

        # isfinited/isnand/isinfd: guard the existing definitions.
        for old, new in [
            (
                b"inline bool isfinited(double x) { return !!std::isfinite(x); }",
                b"#if !defined(__INTEL_COMPILER) && !defined(__INTEL_LLVM_COMPILER)\n"
                b"inline bool isfinited(double x) { return !!std::isfinite(x); }\n"
                b"#endif",
            ),
            (
                b"inline bool isnand(double x)    { return !!std::isnan(x); }",
                b"#if !defined(__INTEL_COMPILER) && !defined(__INTEL_LLVM_COMPILER)\n"
                b"inline bool isnand(double x)    { return !!std::isnan(x); }\n"
                b"#endif",
            ),
            (
                b"inline bool isinfd(double x)    { return !!std::isinf(x); }",
                b"#if !defined(__INTEL_COMPILER) && !defined(__INTEL_LLVM_COMPILER)\n"
                b"inline bool isinfd(double x)    { return !!std::isinf(x); }\n"
                b"#endif",
            ),
        ]:
            content = content.replace(old, new)

        # Add ne_* bool wrappers for the function-pointer tables.  These names
        # do not conflict with anything in Intel math.h.  Functions.hpp is
        # patched below to reference them unconditionally so both Intel and
        # non-Intel builds resolve correctly.
        # fmaxd/fmind use isnand which is guarded away under Intel; patch them
        # to use ne_isnand (defined below) directly.
        content = content.replace(
            b"inline double fmaxd(double x, double y)"
            b"    { return (isnand(x) | isnand(y))? NAN : fmax(x, y); }",
            b"inline double fmaxd(double x, double y)"
            b"    { return (ne_isnand(x) | ne_isnand(y))? NAN : fmax(x, y); }",
        )
        content = content.replace(
            b"inline double fmind(double x, double y)"
            b"    { return (isnand(x) | isnand(y))? NAN : fmin(x, y); }",
            b"inline double fmind(double x, double y)"
            b"    { return (ne_isnand(x) | ne_isnand(y))? NAN : fmin(x, y); }",
        )

        # ne_* wrappers must appear before fmaxd/fmind but we inject them before
        # the closing #endif which is after the #else block.  Instead, inject them
        # right before the fmaxd definition inside the #else block.
        ne_wrappers = (
            b"// ne_* wrappers: bool-returning versions safe under all compilers.\n"
            b"// Intel math.h declares signbitf/isfinited/isnand/isinfd returning int;\n"
            b"// these wrappers avoid the return-type overload conflict.\n"
            b"inline bool ne_signbitf(float x)   { return !!signbit((double)x); }\n"
            b"inline bool ne_signbitd(double x)  { return !!signbit(x); }\n"
            b"inline bool ne_isfinited(double x) { return !!std::isfinite(x); }\n"
            b"inline bool ne_isnand(double x)    { return !!std::isnan(x); }\n"
            b"inline bool ne_isinfd(double x)    { return !!std::isinf(x); }\n"
        )
        # Inject before the fmaxd/fmind block (the "// To handle overloading" comment)
        content = content.replace(
            b"// To handle overloading of fmax/fmin in cmath and match NumPy behaviour for NaNs\n",
            ne_wrappers + b"// To handle overloading of fmax/fmin in cmath and match NumPy behaviour for NaNs\n",
        )

        with open(config, "wb") as f:
            f.write(content)

        # --- patch numexpr/functions.hpp ---
        # Replace the four entries that put int-returning functions into bool(*)
        # typed tables with the ne_* bool wrappers defined above.
        funcs = "numexpr/functions.hpp"
        with open(funcs, "rb") as f:
            fcontent = f.read()
        fcontent = fcontent.replace(b"\r\n", b"\n")
        for old, new in [
            (
                b'FUNC_BD(FUNC_ISNAN_BD,   "isnan_bd",    isnand, vdIsnan)',
                b'FUNC_BD(FUNC_ISNAN_BD,   "isnan_bd",    ne_isnand, vdIsnan)',
            ),
            (
                b'FUNC_BD(FUNC_ISFINITE_BD, "isfinite_bd", isfinited, vdIsfinite)',
                b'FUNC_BD(FUNC_ISFINITE_BD, "isfinite_bd", ne_isfinited, vdIsfinite)',
            ),
            (
                b'FUNC_BD(FUNC_ISINF_BD, "isinf_bd", isinfd, vdIsinf)',
                b'FUNC_BD(FUNC_ISINF_BD, "isinf_bd", ne_isinfd, vdIsinf)',
            ),
            (
                b'FUNC_BD(FUNC_SIGNBIT_BD, "signbit_bd",  signbit, vdSignBit)',
                b'FUNC_BD(FUNC_SIGNBIT_BD, "signbit_bd",  ne_signbitd, vdSignBit)',
            ),
            (
                b'FUNC_BF(FUNC_SIGNBIT_BF, "signbit_bf", signbitf, signbitf2, vsSignBit)',
                b'FUNC_BF(FUNC_SIGNBIT_BF, "signbit_bf", ne_signbitf, signbitf2, vsSignBit)',
            ),
        ]:
            fcontent = fcontent.replace(old, new)
        with open(funcs, "wb") as f:
            f.write(fcontent)
