# Hamulous-Stache
A stache of functions that are meant for modding Plants vs Zombies 2 with other things thrown in. These functions are made by Hamulous and other contributors and are mainly made for usage with Sen 4.0. All of this is coded in python. Below will explain each current function.

## Includes:

# Bulk Costume Integrator:
- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Automatically extracts and formats costume data from Propertysheets.json into two structured output files: one for store product definitions and one for market scheduling.

You will need a full path to a valid Propertysheets.json file from your pvz2 mod's obb.

The script will create:
```
- products_output.json 
- market_schedule_output.json 
(In the same folder as your Propertysheets.json.)
```

# Dialogue Formatter 

- Author: [Jay Krow](https://github.com/jaykrow)
- Purpose: Converts structured dialogue written in .txt format into LawnStrings-compatible JSON-style lines for use in PvZ2 modding

The script will:
```
Converts natural dialogue into structured NARRATIVE_ format
Maps character aliases (e.g. Dave → crazydave)
Applies automatic emotion tags for specific characters (like Greg, Grim, Stilts)
Outputs to a clean, formatted out.txt in the same folder as your input file
```

Input Format Example

```
Alias Dave crazydave 
Alias Penny winnie

Prefix: EPIC_QUEST_SHADOWLURKERS_02_INTRO
{NPC_ENTER:crazydave} {NPC_ENTER:winnie} Penny: User Dave, it appears some alternate zombie threats are coming out of the shadows.
Dave: {EXCITED} Oh no! Not the fog-lurkers!
Dave: {EXCITED} Those guys took our beloved friend GLOOM-SHROOM!
Penny: User Dave, I believe you are mistaken.
Penny: These zombies have only captured the Gloom Vine, not the Gloom-shroom.
Penny: Gloom-shroom is currently enjoying his retirement, according to my data.

Prefix: EPIC_QUEST_SHADOWLURKERS_04_INTRO
Dave: What's with those spooky new tiles on the lawn?
Penny: Data shows that these are Boosting Tiles, User Dave.
Penny: Zombies that step on them can receive toughness, speed, or invincibility boosts.
Dave: Invincibility?! These weird zombie guys just won't play fair!
```

Rules
- Alias <Name> <Replacement> defines speaker ID mappings.
- Prefix: declares the narrative segment.
- {NPC_ENTER:Name} sets NPC entrances.
- Format: <Speaker>: <MoodTag (optional)> <Dialogue>

Drag and drop your .txt dialogue file into the terminal or input and you're done.

The script will create:
```
a(n) out.txt in the same directory as your input file
```

out.txt example:
```
"NARRATIVE_EPIC_QUEST_SHADOWLURKERS_01_INTRO_1",
"{NPC_ENTER:G}{NPC_ENTER:gr}{TIRED:antibullysquad}Yeah what he said!",
```

# Erase Plant Levels

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Strips all plant level data from the PLANTLEVELS.json file to simplify plants to level 1 with no progression.

The script will:
```
- Trim all FloatStats and StringStats values to level 1
- Removing XP and coin upgrade data
- Disabling the leveling system for each plant
- Reducing PlantTier to one entry (if applicable)
```

You will need a full path to a valid PLANTLEVELS.json file from your pvz2 mod's obb.

The script will create:
```
- a new .patch.json file for use in your pvz2 mod.
```

# Zombie Actions Organizer

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Automatically organizes the entries in ZOMBIEACTIONS.json based on their actual usage order in ZOMBIEPROPERTIES.json for easier modding and debugging in PvZ2.

The script will:
```
- Read the Actions field from every zombie in ZOMBIEPROPERTIES.json
- Extracts referenced actions using RTID(...) syntax
- Reorders ZOMBIEACTIONS.json so used actions appear first in the same order as they’re used
- Appends unused actions afterward
```

You will need a full path to a valid ZOMBIEPROPERTIES.json file and a valid ZOMBIEACTIONS.json file from your pvz2 mod's obb.

The script will create:
```
- a clean, organized zombieactions_results.json
```

# Zombie JSON Organizer

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Reorders ZOMBIETYPES.json and ZOMBIEPROPERTIES.json based on the ZombieAlmanacOrder list from PROPERTYSHEETS.json for easier modding and debugging in PvZ2.

The script will:
```
- Read the zombie order from ZombieAlmanacOrder in PROPERTYSHEETS.json
Reorders:
- ZOMBIETYPES.json by TypeName in almanac order
- ZOMBIEPROPERTIES.json by matching aliases to the zombie type's Properties field
```

You will need a full path to a valid ZOMBIETYPES.json file, ZOMBIEPROPERTIES.json file and a valid PROPERTYSHEETS.json file from your pvz2 mod's obb.

The script will create:
```
- a clean, organized zombietypes_results.json
- a clean, organized zombieprops_results.json
```

# LawnStrings Sorter

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Sorts LocStringValues alphabetically in a PvZ2 LawnStrings JSON file to improve readability, consistency, and localization accuracy.


The script will:
```
- Open a .json file containing LawnStrings data
- Finds the LocStringValues array (which holds alternating key/value pairs)
- Alphabetically sorts the strings by their keys
```

You will need a full path to any valid LAWNSTRINGS json file from your pvz2 mod's obb.

The script will create:
```
- a new sorted file with the prefix sorted_
```

# Swap Symbols Tool

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Renames all symbol references and associated files (XML + PNG) used in a PvZ2 animation asset bundle. It updates DOMDocument.xml, library media files, and symbol XMLs based on a user-defined rename map.

Given a symbol_map.json, this script will:
```
- Update all symbol references in DOMDocument.xml
- Renames media PNGs in library/media/ according to the map
- Modifies and renames XML symbol files in the library/ folder
```

You will need a full path to any valid DOMDocument.xml file, library/ folder containing media/ and symbol XMLs

## symbol_map.json example:
```
{
  "zombieConehead": "zombieConehead_Redux",
  "zombieBucket": "zombieBucket_Metal"
}
```

The script will then mass rename everything in your xml project:

Before:
```
DOMDocument.xml
library/
  ├── media/
  │   ├── zombieConehead.png
  ├── zombieConehead.xml
```

After:
```
DOMDocument.xml 
library/
  ├── media/
  │   ├── zombieConehead_Redux.png
  ├── zombieConehead_Redux.xml

```

# A Cool Image Resizer:
- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Batch resizes, trims, and renames PNG images in a folder for asset optimization in game mods or other projects.

You will need a full path to a folder of pngs you'd like to resize, rename, and trim


When prompted:
```
- Enter the folder path with PNG images
- Enter a prefix for the renamed files (e.g., pea)
- Enter a scale percent (e.g., 50 to reduce size by half)
```
The script will:
```
- Resize each PNG
- Trim transparent space
- Rename it according to the pattern
- Save the updated image(s) in the same folder
```

# Export Sprites from PNG

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Automatically extracts and saves individual sprite components from a single sprite sheet PNG, based on transparency and separation.

The script will:
```
- Analyzes a PNG image for non-transparent regions
- Uses BFS (breadth-first search) to identify connected pixel blobs (sprites)
- Crops each sprite to its bounding box
```

You will need a full path to a valid png sprite sheet you would like to separate sprites from

The script then will:
```
- Save each sprite as a separate .png in a /sprites folder next to the source image
```

# PSD Sprite Exporter

- Author: [Hamulous](https://github.com/Hamulous)
- Purpose: Extracts all visible layers from a .psd file and saves them as individual PNG images. Ideal for sprite exporting from Adobe Photoshop files for game development or asset prep.

The script will:
```
- Open a .psd file using psd-tools
- Iterates through all visible, non-group layers
- Renders each layer into a PNG
```

You will need a full path to a valid .psd file

The script will create:
```
- the PNGs in a folder called exported_sprites next to the PSD
```
