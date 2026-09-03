"""Smoke-test an installed essentia-tensorflow wheel by running TensorFlow inference.

The essentia-tensorflow wheels vendor the TensorFlow C library, so nothing else
has to be installed for a TensorFlow-backed algorithm to run. That the vendored
copy is present, has the right architecture, and is actually reachable from the
extension is not visible until one of those algorithms runs, so this loads a
real graph and checks the output.

Run against an interpreter that has the wheel installed, on a stock image or a
clean venv rather than the build machine, so that the check exercises what the
wheel ships and not what the builder happened to have lying around:

    docker run --rm -v "$PWD":/w -w /w python:3.12-slim bash -c \
        'pip install wheelhouse/essentia_tensorflow-*-cp312-*x86_64.whl &&
         python packaging/verify_wheel_effnet.py discogs-effnet-bs64-1.pb'

The audio is synthesised rather than decoded so that FFmpeg is not part of the
measurement; packaging/verify_wheel_audio.py covers the decoding path.
"""

import sys

import numpy as np

import essentia
from essentia.standard import TensorflowPredictEffnetDiscogs

# discogs-effnet expects 16 kHz mono. Ten seconds is several patches, so the
# output has more than one row and a wrong patch/hop configuration shows up.
SAMPLE_RATE = 16000
DURATION_SECONDS = 10

# The embeddings head, PartitionedCall:1, rather than the 400-way style
# classifier on PartitionedCall:0.
EMBEDDINGS_OUTPUT = 'PartitionedCall:1'
EMBEDDINGS_SIZE = 1280


def synthesise():
    """Return a deterministic 10 s 16 kHz mono signal as float32."""
    t = np.arange(SAMPLE_RATE * DURATION_SECONDS, dtype=np.float32) / SAMPLE_RATE
    # A couple of tones plus a slow sweep, so the spectrum is not a single line.
    signal = (0.4 * np.sin(2 * np.pi * 440.0 * t)
              + 0.3 * np.sin(2 * np.pi * 1320.0 * t)
              + 0.2 * np.sin(2 * np.pi * (200.0 + 60.0 * t) * t))
    return np.ascontiguousarray(signal, dtype=np.float32)


def main(argv):
    if len(argv) != 1:
        sys.exit('usage: verify_wheel_effnet.py <discogs-effnet-bs64-1.pb>')

    graph_filename = argv[0]

    print(f'essentia {essentia.__version__}')

    model = TensorflowPredictEffnetDiscogs(graphFilename=graph_filename,
                                           output=EMBEDDINGS_OUTPUT)
    embeddings = model(synthesise())

    print(f'embeddings {embeddings.shape} {embeddings.dtype}')
    print(f'first values {np.array2string(embeddings[0][:5], precision=5)}')

    if embeddings.ndim != 2:
        sys.exit(f'expected a 2-D array, got {embeddings.ndim} dimensions')
    if embeddings.shape[0] < 1:
        sys.exit('the model produced no patches')
    if embeddings.shape[1] != EMBEDDINGS_SIZE:
        sys.exit(f'expected {EMBEDDINGS_SIZE} features per patch, '
                 f'got {embeddings.shape[1]}')
    if not np.isfinite(embeddings).all():
        sys.exit('the embeddings contain NaN or inf')

    print(f'OK: TensorflowPredictEffnetDiscogs returned {embeddings.shape}')


if __name__ == '__main__':
    main(sys.argv[1:])
