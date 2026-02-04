# Volume settings for unpowered speakers
from https://ssb22.user.srcf.net/setup/volume.html
(also [mirrored on GitLab Pages](https://ssb22.gitlab.io/setup/volume.html) just in case)

If a computer needs external sound, the usual advice is to connect active (powered, amplified) loudspeakers, which

* need an extra power source (or USB port),
* can be susceptible to picking up the 217Hz burst frequency from nearby 2G GSM mobile phones on their input cables (unless using a digital protocol for input, like USB, or well-shielded cables; this is less of a concern as the phone networks switch to 4G and 5G), and
* add to the number of things we can forget to switch off when minimising standby load and/or fire risk (unless there’s room for them in the same socket-bank as the computer).

These disadvantages can be worked around by finding a pair of passive (unpowered) speakers designed to connect to the 3.5mm jack, but:

* You will get a poor frequency response, especially in the bass.  E.g. “Hama MB-20” has a specified range of 100Hz-12kHz (the cello goes down to 65Hz, which *can* be heard on these speakers at a sufficient volume setting, although of course its harmonics are heard even at lower volume levels; my tests also showed poorer response in the 100-200Hz and 10-12kHz ranges), and “Sony SRS-P7” has a specified frequency range of 250Hz-10kHz which means the manufacturers barely expected it to go below middle C.
  * Sometimes you can obtain a ‘flatter’ response by compensating for the speaker’s response curve in software (i.e. have the software attenuate the mid-range frequencies to compensate for the speaker’s attenuating the low and high ones), but this is difficult to get right and results in a lower overall maximum volume level.
* You won’t get much “damping factor” (the computer’s on-board amplifier is unlikely to dampen speaker-cone resonance by presenting a relatively-low resistance to the back-currents it generates), because these speakers’ impedance values are typically less than that of the ‘headphones’ socket (e.g. 8 ohms for the Hama, 6 ohms for the Sony, 10 ohms for a Mac Mini which was expecting 30+ ohm headphones).  Therefore, whatever frequency is the natural resonant one for those particular speaker cones may be distorted, unless it’s being cut off the bottom of the unit’s frequency-response range anyway.
* A very real problem with some low-end speakers is the limited range of cone excursion.  One pair of Hama MB-20s I tested exhibited unstable periodic ‘clicks’ (which I think was the coil hitting the rear plate) at 80% volume even in the 250Hz range, and definitely in the sub-100Hz range, so I wouldn’t recommend driving them at over 70% volume—probably less.  These speakers can nominally take 500mW per channel, and running 1.4V RMS across 8 ohms should get about 250mW which is well within their spec (500mW suggests they can take as high as 2V RMS), but if they’re overexerting at 1.4V RMS (even within their specified frequency range) then perhaps the figures should be downgraded to below 100mW per channel.  The fact that 3dB of volume could be recovered if two identical sets are driven through a Y-splitter may be small consolation when you’re entertaining people who want to sit at a distance. 

## Passive Hi-Fi speakers instead
If you find a pair of passive Hi-Fi type speakers (larger than typical computer speakers but still small by Hi-Fi standards), you may wish to try connecting these for a better frequency response (especially in the bass) and probably better performance at volume.  But check the characteristics.

(You no longer have to worry about “magnetic shielding” around computer speakers unless you still use an old CRT or FDD—magnetic hard disks have their own shielding, and damaging them takes something stronger than a speaker magnet.  But I wouldn’t keep a speaker right on top of a hard disk.)

Typical onboard sound circuits are rated to supply a headphones socket with up to 2 watts before the onboard amplifier starts distorting due to saturation.  This is is typically at 1.4V RMS (=2V peak, =4V peak-to-peak), although the Raspberry Pi reportedly uses the lower “line level” standard of 1V RMS and I don’t know what its current-limiters are set to.

I’m not sure if the “2 watts” figure for PCs/Macs is total or per channel—assume ‘total’ to be safe, so 1 watt per channel—but I expect it won’t include the power dissipated in the amplifier itself, as this is known from its own impedance regardless of the load’s, so if things are behaving as specified we just have to set V²/Z < 1 i.e. Z > 2 to ensure no saturation.  In the unlikely event that your speakers are under 2 ohms, you’ll have to compensate by reducing the maximum volume so that the peak voltage (normally 2) does not exceed the ohm rating (1 watt per channel does make the maths easier).


Actual listening loudness in decibels = `SPL + 3*log₂(V²/Z) - 6*log₂`(distance in metres), where SPL (sensitivity) can be 84 for low-end and 90+ for high-end speakers.  If the only thing you want is loudness then it’s probably not worth investing in speakers with higher SPL: a 16-ohm set with SPL=90 would give the same 3dB increase as would connecting *two* of the 8-ohm SPL=84 sets in parallel over a Y-splitter (presenting a 4-ohm impedance to the PC, which is still above its lower limit of 2), and this latter option is almost certainly cheaper.  But the “good” speakers might have better frequency response.

Hi-Fi type speakers are not typically fitted with 3.5mm jacks, so, unless you are able to make up your own connector, you’ll need something like:

* Two “speaker RCA wire to AV phono male RCA connector-jack” adapters, and
* one “3.5mm stereo jack to 2 RCA phono-sockets” lead (it’s best to avoid rigid connectors that have no lead, as these take up a lot of space around the computer’s sockets)

RCA connectors are coloured red for the right-hand speaker, and a small Philips screwdriver is needed for securing the screws in an RCA-wire connector—“Blu-Tack” may be useful to hold in the wires if the screws are too stiff to turn on a low-quality connector (school physics experiments on the electrical conductivity of “Blu-Tack” showed it’s variable across different batches, but at room temperatures and low voltages it should provide high enough resistance to count as only a small reduction in load impedance if a speaker’s terminals both touch the same lump of tack, as long as the stripped parts of the wires don’t touch each other directly), but you might find a Blu-Tack’d connector is easily disturbed by vibrations leading to a loss of volume, so it’s better to order two pairs of connectors so you have spares.  The red wire connects to the + terminal, but many speakers will work either way.

You shouldn’t have to worry about a maximum volume level if the Hi-Fi speakers’ impedance is 8+ and they are rated to be able to take a current of 5 watts or above, although of course you may still wish to keep it down when the neighbours are at home!  (If you are in an upstairs flat, then try to avoid putting loudspeakers on the floor.)

Amazon’s Echo Dot 2 can also drive passive hi-fi speakers to obtain stereo and better sound quality: it’s best run at its maximum volume for this and it’s not very loud.  The later models with 3.5mm sockets (Dot 3 and above) can also do this but there’s less reason to as those later models have better on-board speakers and (unlike the Dot 2) are able to form stereo pairs.

Disclaimer: the above notes are provided in the hope that they are useful, but what you do with your sound is at your own risk—I will not take legal responsibility for damage to equipment, hearing, community etc.

## Copyright and Trademarks
All material © Silas S. Brown unless otherwise stated.
Blu-Tack is a trademark of Bostik SA.
Mac is a trademark of Apple Inc.
Raspberry Pi is a trademark of the Raspberry Pi Foundation.
Any other trademarks I mentioned without realising are trademarks of their respective holders.
