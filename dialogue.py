file_name = 'dialogue.txt'
out_file_name = 'out.txt'

prefix = ""

aliases = {}

bullyemotions = {
    "Greg": "PLAYFUL",
    "Grim": "TIRED",
    "Stilts": "SHOUT",
}

with open(file_name, "r") as file:
    with open(out_file_name, "w") as out_file:
        # Read the contents of the file
        counter = 1

        for line in file:
            line = line.strip()
            if line == "":
                continue

            if line.startswith("Prefix:"):
                counter = 1
                prefix = line[7:]
                prefix = prefix.strip()

                prefix = "NARRATIVE_" + prefix
                out_file.write('\n') # split dialogue into paragraphs
                continue

            if line.startswith("Alias"): # alias Dave crazydave
                linesplit = line.split()
                aliases[linesplit[1].strip()] = linesplit[2].strip()
                continue

            out_file.write("\"" + prefix + f"_{counter}\",\n")
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

                if part.endswith('}') and enter_block_finished == False:
                    enters += part
                    enter_block_finished = True
                    continue

                if part.endswith(":") and speaker == "":
                    character = part[:-1]
                    if character in aliases:
                        character = aliases[character]
                    speaker = character
                    continue
                
                if part.startswith("{"):
                    mood = part[1:-1]
                    continue
                # print(part + " lived")
                dialogue += part + " "
            
            dialogue = dialogue[:-1] # remove the last whitespace
            # print(speaker + " " + dialogue)
            
            # playful is greg, tired is grim and shout is stilts
            if speaker in bullyemotions:
                mood = bullyemotions[speaker]
                speaker = "antibullysquad"

            out_file.write('\"' + enters + '{' + mood + ':' + speaker + '}' + dialogue + '\",\n')

            # out_file.write(currentline + ",\n")