import csv

pdf_data = """
Speech  	0.663131595 
Male speech, man speaking  	0.177051112 
Female speech,  woman 	 0.115134761 
speaking  	
Child speech, kid speaking  	0.233555675 
Conversation  	0.079049014 
Narration, monologue  	0.148160264 
Babbling  	0.29551515 
Speech synthesizer  	0.114881948 
Shout  	0.123608574 
Bellow  	0.115662575 
Whoop  	0.185566455 
Yell  	0.203322187 
Battle cry  	0.21404101 
Children shouting  	0.14569521 
Screaming  	0.218166262 
Whispering  	0.439987093 
Laughter  	0.373072088 
Baby laughter  	0.498326451 
Giggle  	0.231795475 
Snicker  	0.203020319 
Belly laugh  	0.263697952 
Chuckle, chortle  	0.212297976 
Crying, sobbing  	0.250249505 
Baby cry, infant cry  	0.366189182 
Whimper  	0.165533066 
Wail, moan  	0.117786862 
Sigh  	0.121035784 
Singing  	0.334172606 
Choir  	0.310240626 
Yodeling  	0.104060158 
Chant  	0.23072274 
Mantra  	0.296109617 
Male singing  	0.115370326 
Female singing  	0.266682774 
Child singing  	0.292762011 
Synthetic singing  	0.189190939 
Rapping  	0.213257313 
Humming  	0.147413835 
Groan  	0.267993331 
Grunt  	0.183808699 
Whistling  	0.331246257 
Breathing  	0.078809544 
Wheeze  	0.068359815 
Snoring  	0.115220405 
Gasp  	0.144594833 
Pant  	0.068428777 
Snort  	0.077853985 
Cough  	0.324417293 
Throat clearing  	0.255496502 
Sneeze  	0.230125844 
Sniff  	0.079365209 
Run  	0.078879051 
Shuffle  	0.035825808 
Walk, footsteps  	0.097542576 
Chewing, mastication  	0.24013032 
Biting  	0.164163366 
Gargling  	0.043829158 
Stomach rumble  	0.029107671 
Burping, eructation  	0.266600043 
Hiccup  	0.144014791 
Fart  	0.123087049 
Hands  	0.138297305 
Finger snapping  	0.070497356 
Clapping  	0.128759995 
Heart sounds, heartbeat  	0.586156607 
Heart murmur  	0.377441734 
Cheering  	0.211448893 
Applause  	0.139219627 
Chatter  	0.247834355 
Crowd  	0.304168642 
Hubbub, speech noise, speech babble 	 	0.116272435 
Children playing  	0.214131489 
Animal  	0.44654569 
Domestic animals, pets  	0.502729535 
Dog  	0.502826989 
Bark  	0.29924795 
Yip  	0.248220921 
Howl  	0.31447342 
Bow-wow  	0.371089131 
Growling  	0.198315382 
Whimper (dog)  	0.269767046 
Cat  	0.661231399 
Purr  	0.172264501 
Meow  	0.447990417 
Hiss  	0.254105061 
Caterwaul  	0.211083338 
Livestock, farm animals, working animals  	0.25670734
Horse  	0.277501345 
Clip-clop  	0.23132506 
Neigh, whinny  	0.327387959 
Cattle, bovinae  	0.143070012 
Moo  	0.123658635 
Cowbell  	0.067611158 
Pig  	0.152138457 
Oink  	0.110466607 
Goat  	0.425498694 
Bleat  	0.38615489 
Sheep  	0.499358416 
Fowl  	0.287642866 
Chicken, rooster  	0.57516247 
Cluck  	0.37550348 
Crowing, cock-a-doodle-doo  	0.536303699 
Turkey  	0.170065507 
Gobble  	0.143449247 
Duck  	0.250974685 
Quack  	0.175435185 
Goose  	0.283875763 
Honk  	0.276641488 
Wild animals  	0.316515833 
Roaring cats (lions, tigers)  	0.312159359 
Roar  	0.382700235 
Bird  	0.249224812 
Bird vocalization, bird call, bird song  	 	0.11407949 
Chirp, tweet  	0.171352997 
Squawk  	0.022521921 
Pigeon, dove  	0.525361836 
Coo  	0.258235306 
Crow  	0.172924042 
Caw  	0.154051647 
Owl  	0.277525753 
Hoot  	0.057413232 
Bird flight, flapping wings  	0.151714608 
Canidae, dogs, wolves  	0.220703542 
Rodents, rats, mice  	0.114968784 
Mouse  	0.084620617 
Patter  	0.133851618 
Insect  	0.155930132 
Cricket  	0.129208148 
Mosquito  	0.165145859 
Fly, housefly  	0.081412442 
Buzz  	0.052863088 
Bee, wasp, etc.  	0.306852907 
Frog  	0.485871822 
Croak  	0.215655431 
Snake  	0.111441046 
Rattle  	0.081631362 
Whale vocalization  	0.216013104 
Music  	0.695782125 
Musical instrument  	0.664697647 
Plucked string instrument  	0.644903183 
Guitar  	0.677955449 
Electric guitar  	0.265161753 
Bass guitar  	0.214493647 
Acoustic guitar  	0.332311481 
Steel guitar, slide guitar  	0.095357895 
Tapping (guitar technique)  	0.112518124 
Strum  	0.30383411 
Banjo  	0.361035645 
Sitar  	0.366262436 
Mandolin  	0.190164849 
Zither  	0.219142079 
Ukulele  	0.181958601 
Keyboard (musical)  	0.321676046 
Piano  	0.385540247 
Electric piano  	0.325575382 
Organ  	0.194115222 
Electronic organ  	0.28050372 
Hammond organ  	0.356615514 
Synthesizer  	0.275485277 
Sampler  	0.069920674 
Harpsichord  	0.072910741 
Percussion  	0.230211183 
Drum kit  	0.554444551 
Drum machine  	0.107196212 
Drum  	0.325900227 
Snare drum  	0.455587745 
Rimshot  	0.316852182 
Drum roll  	0.297954619 
Bass drum  	0.36236921 
Timpani  	0.303963929 
Tabla  	0.295500129 
Cymbal  	0.285343617 
Hi-hat  	0.32222259 
Wood block  	0.183640361 
Tambourine  	0.151852444 
Rattle (instrument)  	0.177172914 
Maraca  	0.161213964 
Gong  	0.17275995 
Tubular bells  	0.121038929 
Mallet percussion  	0.296782434 
Marimba, xylophone  	0.357874542 
Glockenspiel  	0.317277491 
Vibraphone  	0.085060105 
Steelpan  	0.091474771 
Orchestra  	0.274709433 
Brass instrument  	0.333184689 
French horn  	0.428960562 
Trumpet  	0.424405456 
Trombone  	0.472386688 
Bowed string instrument  	0.274520278 
String section  	0.152847514 
Violin, fiddle  	0.59591496 
Pizzicato  	0.114062063 
Cello  	0.304534048 
Double bass  	0.173844486 
Wind instrument, woodwind instrument 	  	0.183094144 
Flute  	0.437521011 
Saxophone  	0.348937362 
Clarinet  	0.114024296 
Harp  	0.287115008 
Bell  	0.447264761 
Church bell  	0.498801082 
Jingle bell  	0.481084675 
Bicycle bell  	0.237709165 
Tuning fork  	0.152658209 
Chime  	0.203257158 
Wind chime  	0.142850056 
Change ringing (campanology) 	  	0.283088088
Harmonica  	0.203034624 
Accordion  	0.338806301 
Bagpipes  	0.342162341 
Didgeridoo  	0.082724355 
Shofar  	0.181253314 
Theremin  	0.142299175 
Singing bowl  	0.407767326 
Scratching (performance technique) 	 	0.2001753
Pop music  	0.175155237 
Hip hop music  	0.226504967 
Beatboxing  	0.135438621 
Rock music  	0.20140484 
Heavy metal  	0.207650691 
Punk rock  	0.184391364 
Grunge  	0.14775604 
Progressive rock  	0.124065042 
Rock and roll  	0.162180975 
Psychedelic rock  	0.18374382 
Rhythm and blues  	0.114576831 
Soul music  	0.111013003 
Reggae  	0.130258381 
Country  	0.279570192 
Swing music  	0.195873886 
Bluegrass  	0.197946325 
Funk  	0.096758164 
Folk music  	0.183918893 
Middle Eastern music  	0.185409769 
Jazz  	0.210506797 
Disco  	0.115051344 
Classical music  	0.255958617 
Opera  	0.23816818 
Electronic music  	0.412831038 
House music  	0.111430436 
Techno  	0.129632458 
Dubstep  	0.134312242 
Drum and bass  	0.088922143 
Electronica  	0.078854039 
Electronic dance music  	0.093672603 
Ambient music  	0.183921918 
Trance music  	0.152654558 
Music of Latin America 	0.358672321 
Salsa music 	0.522390962 
Flamenco 	0.122381479 
Blues 	0.141842276 
Music for children 	0.312739849 
New-age music 	0.192540139 
Vocal music 	0.168585971 
A capella 	0.164358288 
Music of Africa 	0.102144323 
Afrobeat 	0.086320125 
Christian music 	0.227192894 
Gospel music 	0.184776977 
Music of Asia 	0.14503032 
Carnatic music 	0.315148413 
Music of Bollywood 	0.369802952 
Ska 	0.175568014 
Traditional music 	0.224747136 
Independent music 	0.077284612 
Song 	0.052710533 
Background music 	0.110848658 
Theme music 	0.131275043 
Jingle (music) 	0.098749198 
Soundtrack music 	0.108967468 
Lullaby 	0.168360233 
Video game music 	0.140018523 
Christmas music 	0.131075948 
Dance music 	0.069544785 
Wedding music 	0.064275727 
Happy music 	0.05340232 
Funny music 	0.068387859 
Sad music 	0.141525686 
Tender music 	0.091772437 
Exciting music 	0.060108818 
Angry music 	0.289104104 
Scary music 	0.172716737 
Wind 	0.138315216 
Rustling leaves 	0.055980973 
Wind noise (microphone) 	0.161091596 
Thunderstorm 	0.457061023 
Thunder 	0.563930094 
Water 	0.257889897 
Rain 	0.320453703 
Raindrop 	0.208118558 
Rain on surface 	0.356790185 
Stream 	0.244035527 
Waterfall 	0.246880203 
Ocean 	0.323650539 
Waves, surf 	0.338499546 
Steam 	0.369944096 
Gurgling 	0.096132152 
Fire 	0.063047104 
Crackle 	0.074694604 
Vehicle 	0.61871177 
Boat, Water vehicle 	0.179446802 
Sailboat, sailing ship 	0.187928498 
Rowboat, canoe, kayak 	0.179120854 
Motorboat, speedboat 	0.128375039 
Ship 	0.112537846 
Motor vehicle (road) 	0.162375972 
Car 	0.48143366 
Vehicle horn, car horn, honking 	 	0.384600937 
Toot 	0.386194468 
Car alarm 	0.097251847 
Power windows, electric windows  	0.176437467 	
Skidding 	0.275554746 
Tire squeal 	0.219990492 
Car passing by 	0.115634248 
Race car, auto racing 	0.382500648 
Truck 	0.273021817 
Air brake 	0.138077229 
Air horn, truck horn 	0.218268767 
Reversing beeps 	0.093336672 
Ice cream truck, ice cream van 	0.078854173
Bus 	0.12708573 
Emergency vehicle 	0.351332217 
Police car (siren) 	0.432965875 
Ambulance (siren) 	0.282593876 
Fire engine, fire truck (siren) 	0.278387576 
Motorcycle 	0.20692268 
Traffic noise, roadway noise 	0.102626778 
Rail transport 	0.487690419 
Train 	0.543006361 
Train whistle 	0.324747264 
Train horn  	0.422004044 
Railroad car, train wagon  	0.467045546 
Train wheels squealing  	0.221710682 
Subway, metro, underground  	0.190360218 
Aircraft  	0.299334228 
Aircraft engine  	0.252298236 
Jet engine  	0.296206057 
Propeller, airscrew  	0.16553238 
Helicopter  	0.156141818 
Fixed-wing aircraft, airplane  	0.298614621 
Bicycle  	0.074093737 
Skateboard  	0.17546545 
Engine  	0.387351185 
Light engine (high frequency)  	0.096594892	
Dental drill, dentist's drill  	0.056031898 
Lawn mower  	0.136818618 
Chainsaw  	0.225480139 
Medium engine (mid frequency)  	0.232694268
Heavy engine (low frequency)  	 0.123488508 
Engine knocking  	0.144582197 
Engine starting  	0.354518861 
Idling  	0.290382713 
Accelerating, revving, vroom  	0.203454256 
Door  	0.315597534 
Doorbell  	0.3486166 
Ding-dong  	0.21867843 
Sliding door  	0.17909281 
Slam  	0.189475045 
Knock  	0.085836619 
Tap  	0.147365272 
Squeak  	0.063325681 
Cupboard open or close  	0.084238157 
Drawer open or close  	0.169087112 
Dishes, pots, and pans  	0.447392136 
Cutlery, silverware  	0.400630862 
Chopping (food)  	0.059041321 
Frying (food)  	0.496444315 
Microwave oven  	0.069656625 
Blender  	0.235500246 
Water tap, faucet  	0.303930074 
Sink (filling or washing)  	0.265050173 
Bathtub (filling or washing)  	0.200963676 
Hair dryer  	0.384524018 
Toilet flush  	0.325801611 
Toothbrush  	0.019311575 
Electric toothbrush  	0.1339968 
Vacuum cleaner  	0.19708319 
Zipper (clothing)  	0.06996157 
Keys jangling  	0.189677477 
Coin (dropping)  	0.285103798 
Scissors  	0.132798031 
Electric shaver, electric razor  	0.301772743 
Shuffling cards  	0.070550777 
Typing  	0.554699242 
Typewriter  	0.280794621 
Computer keyboard  	0.617722034 
Writing  	0.050774451 
Alarm  	0.371867567 
Telephone  	0.354798466 
Telephone bell ringing  	0.46751529 
Ringtone  	0.174754292 
Telephone dialing, DTMF  	0.463954329 
Dial tone  	0.54632026 
Busy signal  	0.141894847 
Alarm clock  	0.260299116 
Siren  	0.243918046 
Civil defense siren  	0.289382815 
Buzzer  	0.14346455 
Smoke detector, smoke alarm 	 0.321305007 
Fire alarm  	0.315309227 
Foghorn  	0.071005449 
Whistle  	0.252787769 
Steam whistle  	0.37333259 
Mechanisms  	0.156226665 
Ratchet, pawl  	0.212517902 
Clock  	0.263694137 
Tick  	0.203262269 
Tick-tock  	0.3612324 
Gears  	0.108477362 
Pulleys  	0.018109933 
Sewing machine  	0.425129175 
Mechanical fan  	0.076244779 
Air conditioning  	0.085429914 
Cash register  	0.212127492 
Printer  	0.139732093 
Camera  	0.221891642 
Single-lens reflex camera  	0.094002508 
Tools  	0.270691961 
Hammer  	0.122144006 
Jackhammer  	0.159390241 
Sawing  	0.273562044 
Filing (rasp)  	0.242312476 
Sanding  	0.131467342 
Power tool  	0.27124989 
Drill  	0.327001512 
Explosion  	0.246982485 
Gunshot, gunfire  	0.274078786 
Machine gun  	0.41274935 
Fusillade  	0.242372468 
Artillery fire  	0.239608631 
Cap gun  	0.226551458 
Fireworks  	0.257660568 
Firecracker  	0.240311772 
Burst, pop  	0.14886722 
Eruption  	0.105139807 
Boom  	0.418254107 
Wood  	0.258548886 
Chop  	0.130496129 
Splinter  	0.044245046 
Crack  	0.100706682 
Glass  	0.167997286 
Chink, clink  	0.173519179 
Shatter  	0.398548841 
Liquid  	0.204431549 
Splash, splatter  	0.339683443 
Slosh  	0.140614495 
Squish  	0.090667889 
Drip  	0.159935892 
Pour  	0.21663636 
Trickle, dribble  	0.177726403 
Gush  	0.101941027 
Fill (with liquid)  	0.134252861 
Spray  	0.101014763 
Pump (liquid)  	0.096536674 
Stir  	0.502062023 
Boiling  	0.072351612 
Sonar  	0.224648193 
Arrow  	0.133135632 
Whoosh, swoosh, swish  	0.08842659 
Thump, thud  	0.184166759 
Thunk  	0.356837004 
Electronic tuner  	0.174774379 
Effects unit  	0.325970948 
Chorus effect  	0.112906352 
Basketball bounce  	0.176170349 
Bang  	0.077220127 
Slap, smack  	0.146909401 
Whack, thwack  	0.183542639 
Smash, crash  	0.161734805 
Breaking  	0.343452632 
Bouncing  	0.026883934 
Whip  	0.115855664 
Flap  	0.040026832 
Scratch  	0.116082206 
Scrape  	0.085538633 
Rub  	0.319610268 
Roll  	0.085861668 
Crushing  	0.045119323 
Crumpling, crinkling  	0.453958571 
Tearing  	0.247198448 
Beep, bleep  	0.207098469 
Ping  	0.060113803 
Ding  	0.259459108 
Clang  	0.09959434 
Squeal  	0.061658584 
Creak  	0.011485431 
Rustle  	0.062489577 
Whir  	0.070328631 
Clatter  	0.086530887 
Sizzle  	0.379612952 
Clicking  	0.095380723 
Clickety-clack  	0.315681338 
Rumble  	0.088044569 
Plop  	0.383814484 
Jingle, tinkle  	0.218950465 
Hum  	0.195067123 
Zing  	0.091545887 
Boing  	0.526967525 
Crunch  	0.176332623 
Silence 		0.438278347 
Sine wave 		0.230977759 
Harmonic 		0.027165079 
Chirp tone 		0.128388375 
Sound effect 		0.088372767 
Pulse 		0.023377132 
Inside, small room 		0.289901823 
Inside, large room or hall 		0.110736884 
Inside, public space 		0.085936405 
Outside, urban or manmade 		0.152951151 
Outside, rural or natural 		0.130573094 
Reverberation 		0.068756551 
Echo 		0.082826756 
Noise 		0.113706246 
Environmental noise 		0.165826917 
Static 		0.080373839 
Mains hum 		0.05315442 
Distortion 		0.165851399 
Sidetone 		0.059336774 
Cacophony 		0.077936336 
White noise 		0.131008565 
Pink noise 		0.430678964 
Throbbing 		0.233170211 
Vibration 		0.129959524 
Television 		0.085169442 
Radio 		0.132174551 
Field recording 		0.051390097 
"""
map_of_classes = {}
for line in pdf_data.split("\n"):
    columns = line.strip().split("\t")
    if len(columns) >= 2:
        if "." not in columns[-1]:
            raise Exception("Missing coefficient in " + line)
        map_of_classes[" ".join(columns[:-1]).strip()] = columns[-1]


with open("yamnet/yamnet_class_threshold_map.csv", "w") as out_csv_file:
    with open("yamnet/yamnet_class_map.csv") as csv_file:
        reader = csv.reader(csv_file)
        writer = csv.writer(out_csv_file)
        next(reader)   # Skip header
        writer.writerow(["index", "mid", "display_name", "threshold"])
        for (index, mid, display_name) in reader:
            coefficient = map_of_classes.get(display_name, None)
            if coefficient is None:
                raise Exception("Cannot find " + display_name)
            writer.writerow([index, mid, display_name, coefficient])

