#!/bin/bash
set -e -x

# Build tools if using original quay.io/pypa/manylinux1_* docker images
# (already built in mtgupf/essentia-builds images)
#/io/travis/build_tools.sh

# Build static 3rdparty dependencies
# (already built in mtgupf/essentia-builds images)
#/io/packaging/build_3rdparty_static_debian.sh --with-gaia

# Location of the dependencies in essentia-builds docker images
# ...is already set in the docker images
#PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
#PKG_CONFIG_PATH=/io/packaging/debian_3rdparty/lib/pkgconfig

# To prevent errors parsing version with `git describe`.
git config --global --add safe.directory /io

# The build image's system Python drives waf; do not depend on a removed
# /opt/python/cp36 interpreter. Wheels require Python >=3.9 (NumPy >=1.25).
PYBIN="$(dirname "$(command -v python3)")"
python_bins=()
for candidate in /opt/python/cp3*-cp3*/bin; do
    [[ -x "$candidate/python" ]] || continue
    case "$candidate" in
        */cp3[0-8]-*|*t-*) continue ;;
    esac
    python_bins+=("$candidate")
done
if [[ ${#python_bins[@]} -eq 0 ]]; then
    echo "No supported CPython interpreters found in /opt/python" >&2
    exit 1
fi

cd /io

# The legacy i686 image still contains pre-send/receive FFmpeg headers. Build
# the repository-pinned FFmpeg when the image lacks the API used by AudioLoader.
if ! pkg-config --atleast-version=61 libavcodec; then
    (cd packaging/debian_3rdparty && PREFIX=/usr/local ./build_ffmpeg.sh)
fi

if [[ $WITH_TENSORFLOW ]]; then
    PROJECT_NAME='essentia-tensorflow'
    "${PYBIN}/python" waf configure --with-gaia --with-tensorflow --build-static --static-dependencies --pkg-config-path="${PKG_CONFIG_PATH}"
else
    PROJECT_NAME='essentia'
    "${PYBIN}/python" waf configure --with-gaia --build-static --static-dependencies --pkg-config-path="${PKG_CONFIG_PATH}"
fi

"${PYBIN}/python" waf
"${PYBIN}/python" waf install
cd -

# Compile wheels
for PYBIN in "${python_bins[@]}"; do
    # Resolve a supported NumPy release for each interpreter instead of old
    # per-version pins that predate Python 3.11 and the current build backend.
    "${PYBIN}/python" -m pip install 'numpy>=1.25'

    ESSENTIA_WHEEL_SKIP_3RDPARTY=1 ESSENTIA_WHEEL_ONLY_PYTHON=1 \
    ESSENTIA_PROJECT_NAME="${PROJECT_NAME}" "${PYBIN}/pip" wheel /io/ -w wheelhouse/

    # Bundle external shared libraries into the essentia wheel now because
    # the tensorflow libraries are specific for each package version
    for whl in wheelhouse/*.whl; do
        PYVERSION=$( echo "$PYBIN" |cut -d/ -f4 )

        if [[ "$whl" == wheelhouse/essentia*"${PYVERSION}"* ]];
        then
            auditwheel repair "$whl" -w /io/wheelhouse/
        fi
    done
done

# Bundle external shared libraries into the rest of wheels
for whl in wheelhouse/*.whl; do
    if [[ "$whl" != wheelhouse/essentia* ]]; then
    # The wheels that already have `manylinux*` or `none-any`
    # (not OS-specific and suitable to any processor architecture) tags do not need
    # to be repaired with auditwheel. This applies to this known bug for six package
    # https://github.com/pypa/python-manylinux-demo/issues/7
        if [[ "$whl" != wheelhouse/*manylinux* && "$whl" != wheelhouse/*-none-any* ]];
        then
            auditwheel repair "$whl" -w /io/wheelhouse/
        else
            cp "$whl" /io/wheelhouse/
        fi
    fi
done

# Install and test
for PYBIN in "${python_bins[@]}"; do
    "${PYBIN}/pip" install "${PROJECT_NAME}" --no-index -f /io/wheelhouse
    if [[ $WITH_TENSORFLOW ]]; then
    # Test that essentia can be imported along with the latest TensorFlow for each Python version
        "${PYBIN}/pip" install tensorflow
        (cd "$HOME"; ${PYBIN}/python -c 'import essentia; import essentia.standard; import essentia.streaming; import tensorflow')
    else
        (cd "$HOME"; ${PYBIN}/python -c 'import essentia; import essentia.standard; import essentia.streaming')
    fi
done
