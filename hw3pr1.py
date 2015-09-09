# -*- coding: utf-8 -*-
import random
import math
from csaudio import play, readwav, writewav


def scale(L, scale_factor):
    '''Given a list L, scales each element of the list by scale_factor'''

    return [scale_factor * n for n in L]

def wrap1( L ):
    """ Given a list L, shifts each element in L to the right by 1 
        (the element at the end of the list wraps around to the beginning)
    """

    # I changed the body of this function to call wrapN, 
    # so that I can reuse the code I wrote for that problem 
    return wrapN(L, 1)   


def wrapN(L, N):
    """ Given a list L, shifts each element in L to the right by N 
        (elements at the end of the list wrap around to the beginning)
    """

    length = len(N)
    return [ L[i-N] for i in range(length) ]


def add_2(L, M):
    '''Given two lists, L and M, adds their respective elements. If the two 
       lists have different lengths, the function truncates the result so that 
       it is as long as the shorter list.
    '''

    length = min(len(L), len(M))  # find the shorter length
    return [ L[i] + M[i] for i in range(length) ]
    
    # Here's an alternative solution that uses the built-in zip function,
    # which truncates for us and creates tuples of the corresponding elements.
    #return [l + m for (l, m) in zip(L, M)]    


def add_scale_2(L, M, L_scale, M_scale):
    '''Given two lists, L and M, and two scale factors, L_scale and M_scale, 
       scales each list by its respective scale factor, then adds the 
       results, pairwise. If the two  lists have different lengths, the function 
       truncates the result so that it is as long as the shorter list.
    '''
    
    return add_2(scale(L, L_scale), scale(M, M_scale))  # yay for code re-use!


# generalized versions of add_2 and add_scale_2

def add_N(lists):
    '''Given a list of lists, adds their respective elements. If the two 
       lists have different lengths, the function truncates the result so that 
       it is as long as the shortest list.
    '''
    
    return map(sum, apply(zip, lists)) # lots of higher-order functions here!


def add_scale_N(lists, scaleFactors):
    '''Given a list of lists and a list of scale factors, scales each list by 
       its respective scale factor, then sums the results, element-wise. If the 
       lists have different lengths, the function  truncates the result so that 
       it is as long as the shortest list.
    '''
    
    scaledLists = [scale(l, f) for (l, f) in zip(lists, scaleFactors)]
    return add_N(scaledLists)


# Helper function:  randomize
def randomize( x, chance_of_replacing ):
    """ randomize takes in an original value, x
        and a fraction named chance_of_replacing.

        With the "chance_of_replacing" chance, it
        should return a random float from -32767 to 32767.

        Otherwise, it should return x (not replacing it).
    """
    r = random.uniform(0,1)
    if r < chance_of_replacing:
        return random.uniform(-32768,32767)
    else:
        return x
    

def replace_some(L, chance_of_replacing):
    '''Given a list L, returns a new list L' where each element in L has a 
       chance_of_replacing chance of being replaced with a random, 
       floating-point value in the range -32767 to 32767.
    '''

    return [randomize(e, chance_of_replacing) for e in L]


################################################################################
# below are functions that relate to sound-processing ...
#
# I've re-organized the code so that we can compose the sound-processing 
# operations. Each operation has a modOp function, which takes a tuple that
# contains samples & sampling rate. The function performs the operation, and 
# returns the new samples and sampling rate. A separate function wraps each 
# modOp. This function takes a filename and additional arguments, opens the 
# file, reads the data, calls the corresponding modOp function, writes the 
# results to an output file, and plays the result.
################################################################################
    
# helper functions

def playNewSound( (data, rate), outputFilename='out.wav'):
    '''Given a (sample, sampling rate) tuple and the name of an output file, 
       the function will write the sound data to the output file and play it.
    '''

    print "Playing new sound..."
    writewav(data, rate, outputFilename)
    play(outputFilename)


def combineFiles(filenames, combinator, outputFilename="out.wav"):
    '''Given a list of sound files, combines the sounds in those files,
       according to the supplied function, and plays the result.

       The function expects one argument: a list of sound data tuples.
    '''
    
    print "Reading in the sound data..."
    data = map(readwav, filenames)
    
    print "Computing new sound..."
    newSound = combinator(data)
    
    playNewSound(newSound, outputFilename)


def modifyFile(inputFilename, function, outputFilename="out.wav"):
    '''Modifies the sounds in a file, according to the supplied function, and
       plays the result.

       The function expects one argument: a tuple of sound data.
    '''

    # modifying one file is a specific case of a more general version:
    # combining a modification of multiple files
    combineFiles([inputFilename], lambda l: function(l[0]), outputFilename)


# changing a sound's speed 

def modChangeSpeed( (samples, rate), newRate ):
    '''changes a sound's sampling rate'''

    return (samples, newRate)


def changeSpeed(filename, newsr):
    '''plays an audio file at a different speed'''
    
    modifyFile(filename, lambda sound: modChangeSpeed(sound, newsr))
    

# flip-flopping a sound

def modFlipFlop( (samples, rate) ):
    '''swaps the halves of a sound'''

    midpoint = len(samples) / 2
    newSamples = samples[midpoint:] + samples[:midpoint]
    return (newSamples, rate)


def flipflop(filename):
    '''swaps the halves of an audio file and plays the new sound'''
    
    modifyFile(filename, modFlipFlop)


# reversing a sound

def modReverse( (samples, rate) ):
    '''reverses a sound'''

    return (samples[::-1], rate)


def reverse(filename):
    '''plays an audio file backwards'''
    
    modifyFile(filename, modReverse)


# changing the volume

def modVolume( (samples, rate), scale_factor ):
    '''scales a sound's volume by scale_factor'''

    return scale(samples, scale_factor), rate


def volume(filename, scale_factor):
    '''plays an audio file, with the original volume scaled by scale_factor'''

    modifyFile(filename, lambda sound: modVolume(sound, scale_factor))


# adding static

def modStatic( (samples, rate), probability_of_static ):
    '''replaces each sample with static, according to the given probability'''

    return replace_some(samples, probability_of_static), rate


def static(filename, probability_of_static):
    '''plays an audio file an replaces each sample with static, according to
       the given probability'''
       
    modifyFile(filename, lambda sound: modStatic(sound, probability_of_static))


# overlaying multiple sounds

def overlayN(sounds):
    '''given a list of sounds, overlay them into a single sound'''
    
    # IMPORTANT!
    # we want each sound to make a 1 / N contribution to the final sound, 
    # where N is the number of sounds
    scaleBack = 1.0 / len(sounds) 
    
    # separate the samples from the rates
    samples, rates = apply(zip, sounds)
    
    # scale and sum the sounds
    scaleFactors = [scaleBack] * len(samples)
    newSound = add_scale_N(samples, scaleFactors)
    
    # use the first stream's sample rate as the sample rate for the new sounds
    newRate = rates[0]

    return (newSound, newRate)


def overlay(filename1, filename2):
    '''overlays the sounds from two files and plays them'''

    sounds = [readwav(filename1), readwav(filename2)]
    newSound = overlayN(sounds)
    playNewSound(newSound)


# echo

def modEcho( (samples, rate), time_delay ):
    '''adds an echo effect to a sound.
    
       The time_delay parameter determines the echo's latency.
    '''

    # Echo works by overlaying the sound with a copy of itself.
    # The copy is padded by silence whose duration is determined by time_delay.

    numSilentSamples = int(rate * time_delay)   # how long is the silence?
    silentSamples = [0] * numSilentSamples      # make the silence
    paddedSamples = silentSamples + samples     # pad the sound with silence

    # prepare to overlay
    sound = (samples, rate)    
    echoedSound = (paddedSamples, rate)
    
    return overlayN([sound, echoedSound])


def echo(filename, time_delay):
    '''adds an echo effect to a sound and plays it'''
    
    modifyFile(filename, lambda d: modEcho(d, time_delay))


# tones

def gen_pure_tone(freq, seconds):
    """ pure_tone returns the y-values of a cosine wave
        whose frequency is freq Hertz.
        It returns nsamples values, taken once every 1/44100 of a second;
        thus, the sampling rate is 44100 Hertz.
        0.5 second (22050 samples) is probably enough.
    """
    sr = 44100
    # how many data samples to create
    nsamples = int(seconds*sr) # rounds down
    # our frequency-scaling coefficient, f
    f = 2*math.pi/sr           # converts from samples to Hz
    # our amplitude-scaling coefficient, a
    a = 32767.0
    # the sound's air-pressure samples
    samps = [ a*math.sin(f*n*freq) for n in range(nsamples) ]
    # return both...
    return samps, sr


def pure_tone(freq, time_in_seconds):
    """ plays a pure tone of frequence freq for time_in_seconds seconds """

    print "Generating tone..."
    tone = gen_pure_tone(freq, time_in_seconds)
    playNewSound(tone)


# chords

def chord(f1, f2, f3, time_in_seconds):
    '''plays a chord composed of three frequencies, for a given duration'''
    
    print "Generating tones..."
    tones = [gen_pure_tone(freq, time_in_seconds) for freq in (f1, f2, f3)]
    
    print "Generating chord..."
    sound = overlayN(tones) 
    
    playNewSound(sound)


# BONUS: melodies!

def makeMelody(notes):
    '''given a list of notes, returns a melody of those notes
       
       Each note is represented as a string (see the body of this function).
    '''
    
    # a dictionary that maps note names to frequencies
    # http://en.wikipedia.org/wiki/Piano_key_frequencies
    TONES = {'A'  : 440.000,
             'A#' : 466.164,
             'B'  : 493.883,
             'C'  : 523.251,
             'C#' : 554.365,
             'D'  : 587.330,
             'D#' : 622.254,
             'E'  : 659.255,
             'F'  : 698.456,
             'F#' : 739.989,
             'G'  : 783.991,
             'G#' : 783.991 }
    TONES['A♭'] = TONES['G#']
    TONES['B♭'] = TONES['A#']
    TONES['D♭'] = TONES['C#']
    TONES['E♭'] = TONES['D#']
    TONES['G♭'] = TONES['F#']

    # seconds per note
    DURATION = .5   
    
    # generate the tones
    tones = [gen_pure_tone(TONES[n], DURATION) for n in notes]

    # separate the samples from the rates
    samples, rates = apply(zip, tones)
    
    # flatten the list of samples into a single list
    melody = reduce(list.__add__, samples)
    
    # use the rate of the first sample as the rate of the melody
    rate = rates[0]
    
    return (melody, rate)


def twinkle():
    '''Plays a simple version of "Twinkle, twinkle little star"'''
    
    part1 = [ 'A',  'A',  'E',  'E',  'F#', 'F#', 'E',
              'D',  'D',  'C#', 'C#', 'B',   'B', 'A'  ] 
    part2 = [ 'E',  'E',  'D',  'D',  'C#', 'C#', 'B'  ]
    
    song = part1 + part2 + part2 + part1
    
    playNewSound(makeMelody(song))
    