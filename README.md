# Hamulous-Stache
An Archive of Python Scripts I've made (Mostly for Pvz2 Modding help)

Archive Includes:
- A script that organizes Zombie Types and Zombie Properties based on what the order is in PropertySheets
- A Bulk Costume integrator which helps out with the tedious tasks of adding costumes in the shop
- Sort Lawnstrings, which sorts your lawn strings file in alphabetical order
- Erase Plant levels, which believe it or not, erases the plant levels
- A Cool Image Resizer, which is able to Resize images, rename them, and trim any excess in said images 
- Export Sprites, which is able to look at any sprite sheet and extract its assets into individual images
- PSD Exporter, which is able to extract all the layers of a PSD file using [psd-tools](https://github.com/psd-tools/psd-tools)
- DialogueLawnFormatter, which is able to convert naturally written dialogue into the Pvz2's LawnString format (Written by: [Jay Krow](https://github.com/jaykrow))
# DialogueLawnFormatter Example:
- Start each section with a Prefix: line
- Use Alias lines to define character name mappings
- Use {NPC_ENTER:Name} to denote character entrances
```txt
CharacterName: {OptionalMoodTag} Dialogue text here
```

Then run the script with your `dialogue.txt` file in the same directory, then you're done!
