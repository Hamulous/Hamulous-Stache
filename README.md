# Hamulous-Stache
An Archive of Python Scripts I've made (Mostly for Pvz2 Modding help)

Archive Includes:
- A script that organizes Zombie Types and Zombie Properties based on what the order is in PropertySheets
- A script that organizes Zombie Actions based on what the order is in ZombieProperties
- A Bulk Costume integrator which helps out with the tedious tasks of adding costumes in the shop
- Sort Lawnstrings, which sorts your lawn strings file in alphabetical order
- Erase Plant levels, which believe it or not, erases the plant levels
- A Cool Image Resizer, which is able to Resize images, rename them, and trim any excess in said images 
- Export Sprites, which is able to look at any sprite sheet and extract its assets into individual images
- PSD Exporter, which is able to extract all the layers of a PSD file using [psd-tools](https://github.com/psd-tools/psd-tools)
- DialogueLawnFormatter, which is able to convert naturally written dialogue into Pvz2's LawnString format (Written by: [Jay Krow](https://github.com/jaykrow))
# DialogueLawnFormatter Example:
- Start each section with a Prefix: line
- Use Alias lines to define character name mappings
- Use {NPC_ENTER:Name} to denote character entrances
```txt
CharacterName: {OptionalMoodTag} Dialogue text here

Better Example:
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

Then run the script with your `dialogue.txt` file in the same directory, then you're done!
