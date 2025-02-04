from google.cloud import translate_v2 as translate
import sys
import html
from term import term
import os
from collections import defaultdict
FACTORIO_LANGUAGES=[
    'af',
    'en',
    'be',
    'bg',
    'ca',
    'cs',
    'da',
    'de',
    'el',
    'eo',
    'es',
    'et',
    'eu',
    'fa',
    'fi',
    'fr',
    'gaa',
    'hr',
    'hu',
    'id',
    'is',
    'it',
    'ja',
    'ka',
    'kk',
    'ko',
    'it',
    'lv',
    'nl',
    'no',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'sk',
    'sl',
    'sr',
    'sv-SE',
    'th',
    'tr',
    'uk',
    'vi',
    'zh-CN',
    'zh-TW'
]
# Read file
inputFileName = ""
if(len(sys.argv)<2):
    inputFileName = input("Please input the original .cfg file to be translated: ")
else:
    inputFileName = sys.argv[1]

# Try to open filename
try:
    inputFile = open(inputFileName,"r")
except FileNotFoundError:
    print("File could not be opened")
    exit(1)

# Parse to find terms to translate
print("Parsing input file...")
termList = []
# Saving a copy of the original file is a quick and easy way to re-arrange it in its original form after translation
originalFile = []
for line in inputFile:
    originalFile.append(line)
    if(line[0]!="[" and line[0] != "\n"): # This is a line with a term
        equalsLocation = line.find("=")
        termList.append(term(line[equalsLocation+1:])) # Add term without label or endline

translate_client = translate.Client()
# Obtain list of translated terms from Google API
availableAPILanguages = translate_client.get_languages()
offeredLanguageList = []
for language in availableAPILanguages:
    if(language["language"] in FACTORIO_LANGUAGES):
        offeredLanguageList.append(language)

leftHalf = offeredLanguageList[:int(len(offeredLanguageList)/2)]
rightHalf = (offeredLanguageList[int(len(offeredLanguageList)/2):])
zipped = zip(leftHalf,rightHalf)
maxlen = len(max(leftHalf, key=len))
print("===========================================================================")
for l,r in zipped:
    # Assemble language titles for this line
    leftTitle = "{} ({})".format(l["name"],l["language"])
    rightTitle = "{} ({})".format(r["name"],r["language"]) 
    # Display separated uniformly. Lots of space to accomodate 'Chinese (Traditional) (zh-TW)'
    print('{0:35}  {1}'.format(leftTitle, rightTitle))
    # Confusing naming convention here but 'language' refers to the shorthand letter code like 'en'
print("===========================================================================")
print("This is the full list of languages offered by Factorio's base localization as well as their associated language codes. Please input a comma separated list of the language codes you would like to generate localization for.")
desiredLanguagesInput = input("To select every language, type \"ALL\": ").replace(" ", "")
desiredLanguages = []
if(desiredLanguagesInput!='ALL'):
    desiredLanguagesList = desiredLanguagesInput.split(',')
    notRecognized = []
    desiredLanguages = []
    for lang in desiredLanguagesList:
        if(lang in FACTORIO_LANGUAGES): desiredLanguages.append(lang)
        else: notRecognized.append(lang)
    if(len(notRecognized)>0):
        print("The following language codes were not recognized: {}".format(notRecognized))
else:
    desiredLanguages = FACTORIO_LANGUAGES

# Translation Stage
print("Translating...")
# Assemble list of terms to translate from our term objects
processedTerms = []
for t in termList: # t is a 'term' object which has its parameters automatically processed on construction
    processedTerms.append(t.text)


resultsDictionary = defaultdict()
for language in desiredLanguages:

    result = translate_client.translate(processedTerms, target_language=language)
    translatedTerms = []
    for t in result:
        # Google Translate returns translations in an html format, requires a slight tweak for apostrophes
        translatedTerms.append(html.unescape(t["translatedText"]))
    resultsDictionary[language] = translatedTerms

# Now re-bind all the parameters into the terms\

for language in resultsDictionary.keys():
    for t in range(len(resultsDictionary[language])):
        # Recall that the termList contains objects that hold onto their parameters
        termData = termList[t]
        for p in range(len(termData.parameterList)):
            resultsDictionary[language][t]=resultsDictionary[language][t].replace("P{}".format(p),termData.parameterList[p])



# Create locale directory based on contents of resultsDictionary
for language in resultsDictionary.keys():
    # Create new language directory
    os.mkdir("locale/{}".format(language))
    # Create new config file within that directory
    configFile = open("locale/{}/{}".format(language,inputFileName),'w',encoding="utf-8")
    termIndex = 0
    for line in originalFile: # Copy original file structure but replace terms with translated terms.
        if(line[0]=="[" or line[0] == "\n"):
            configFile.write(line)
        else:
            equalsLocation = line.find("=")
            configFile.write("{}={}".format(line[:equalsLocation],resultsDictionary[language][termIndex]))
            termIndex+=1
    configFile.close()
print("Translation complete successfully")
input("Press ENTER to close...")