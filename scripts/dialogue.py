import os

prefix = ""
aliases = {}

bullyemotions = {
    "Greg": "PLAYFUL",
    "Grim": "TIRED",
    "Stilts": "SHOUT",
}

file_name = input("Drag and drop the dialogue .txt file here: ").strip('"')
out_file_name = os.path.join(os.path.dirname(file_name), "out.txt")

with open(file_name, "r", encoding="utf-8") as file:
    with open(out_file_name, "w", encoding="utf-8") as out_file:
        counter = 1

        for line in file:
            line = line.strip()
            if line == "":
                continue

            if line.startswith("Prefix:"):
                counter = 1
                prefix = line[7:].strip()
                prefix = "NARRATIVE_" + prefix
                out_file.write('\n')
                continue

            if line.startswith("Alias"):
                linesplit = line.split()
                aliases[linesplit[1].strip()] = linesplit[2].strip()
                continue

            out_file.write(f"\"{prefix}_{counter}\",\n")
            counter += 1

            enters = ""
            linesplit = line.split()
            speaker = ""
            mood = "SAY"
            dialogue = ""
            enter_block_finished = True

            for part in linesplit:
                if part.startswith("{NPC_ENTER:") or part.startswith("{NPC_EXIT"):
                    enters += part
                    if not part.endswith('}'):
                        enter_block_finished = False
                    continue

                if part.endswith('}') and not enter_block_finished:
                    enters += part
                    enter_block_finished = True
                    continue

                if part.endswith(":") and speaker == "":
                    character = part[:-1]
                    speaker = aliases.get(character, character)
                    continue

                if part.startswith("{"):
                    mood = part[1:-1]
                    continue

                dialogue += part + " "

            dialogue = dialogue.strip()

            if speaker in bullyemotions:
                mood = bullyemotions[speaker]
                speaker = "antibullysquad"

            out_file.write(f"\"{enters}{{{mood}:{speaker}}}{dialogue}\",\n")

print(f"\nFormatted dialogue saved to: {out_file_name}")
