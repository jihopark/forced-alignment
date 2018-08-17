# scripts for voice activation detection (VAD)
import collections
import contextlib
import sys
import wave
import webrtcvad
import numpy as np

from noise_reduction.noise import reduce_noise_power, reduce_noise_centroid_s
from noise_reduction.noise import reduce_noise_centroid_mb, reduce_noise_mfcc_down, reduce_noise_mfcc_up, reduce_noise_median
from noise_reduction.noise import trim_silence, output_file

def get_vad_object(_mode):
    VAD = webrtcvad.Vad()
    VAD.set_mode(_mode)
    print("loaded VAD object. setting mode to %s" % _mode)
    return VAD

# https://github.com/wiseman/py-webrtcvad/blob/master/example.py
def read_wave(path):
    """Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate

# https://stackoverflow.com/questions/50231266/raw-wav-bytes-to-uint-array-or-some-other-format
# PCM audio to librosa format
def byte_to_float(byte_string):
    return np.fromstring(byte_string, dtype=np.int16)/2**15

# librosa format to PCM audio format
def float_to_byte(float_array):
    return (2**15 * float_array).astype(np.uint16).tostring()


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)
        print("wrote a new file to %s" % path)

class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(vad, sample_rate, frame_duration_ms,
                  padding_duration_ms, frames):
    """Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.
    Arguments:
    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).
    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        #sys.stdout.write('1' if is_speech else '0')
        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
  #              sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
 #               sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
#    if triggered:
#        sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
#    sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

def denoise(vad_obj, audio=None, sample_rate=None, filename=None,
            frame_length_ms=30, padding_duration_ms=300):
    assert filename or (audio and sample_rate)
    if filename is not None:
        audio, sample_rate = read_wave(filename)
    segments = vad_collector(vad_obj, sample_rate, frame_length_ms,
                             padding_duration_ms,
                             list(frame_generator(frame_length_ms, audio, sample_rate)))
    #name, ext = filename.split(".")
    #assert ext == "wav"
    #write_wave(name + "_denoise.wav", b''.join(segments), sample_rate)
    return b''.join(segments), sample_rate

def apply_noise_reduction_then_vad(vad_obj, audio, sr, method):
    if method == "POWER":
        y_reduced = reduce_noise_power(audio, sr)
    elif method == "CENTROID_S":
        y_reduced = reduce_noise_centroid_s(audio, sr)
    elif method == "CENTROID_MB":
        y_reduced = reduce_noise_centroid_mb(audio, sr)
    elif method == "MFCC_UP":
        y_reduced = reduce_noise_mfcc_up(audio, sr)
    elif method == "MFCC_DOWN":
        y_reduced = reduce_noise_mfcc_down(audio, sr)
    elif method == "MEDIAN":
        y_reduced = reduce_noise_median(audio, sr)
    y_reduced, time_trimmed = trim_silence(y_reduced)
    denoised, sr = denoise(vad_obj, audio=float_to_byte(y_reduced),
							sample_rate=sr,
							padding_duration_ms=100, frame_length_ms=10)
    return byte_to_float(denoised), sr

