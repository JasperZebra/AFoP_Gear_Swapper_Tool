![GitHub release (latest by date)](https://img.shields.io/github/v/release/JasperZebra/AFoP_Gear_Swapper_Tool?style=for-the-badge&logo=github&color=00ffff&logoColor=white&labelColor=1a4d66)
![Total Downloads](https://img.shields.io/github/downloads/JasperZebra/AFoP_Gear_Swapper_Tool/total?style=for-the-badge&logo=github&color=00ffff&logoColor=white&labelColor=1a4d66)
![Platform](https://img.shields.io/badge/platform-windows-00ffff?style=for-the-badge&logo=windows&logoColor=00ffff&labelColor=1a4d66)
![Made for](https://img.shields.io/badge/made%20for-Avatar:_Frontiers_of_Pandora-00ffff?style=for-the-badge&logo=gamepad&logoColor=00ffff&labelColor=1a4d66)
![Tool Type](https://img.shields.io/badge/type-gear%20swapper-00ffff?style=for-the-badge&logo=package&logoColor=00ffff&labelColor=1a4d66)

# AFoP Mgraphobject Swapper
A lightweight GUI utility for swapping gear models in **Avatar: Frontiers of Pandora** using `.mgraphobject` file replacement.

<img width="1445" height="899" alt="image" src="https://github.com/user-attachments/assets/2cfcf960-1c7f-4312-8e2a-94929d6c67c1" />


## How to Use

1. **Set your mod folder** — point it to the folder inside your mod where the swapped file should land.
   - This should match the object type you're swapping, e.g. `blue\graph objects\gear` for gear, `blue\graph objects\weapon` for weapons, and so on.
   - This is your **output folder** — the swapped file will be copied here.

2. **Set your source file** — browse to the `.mgraphobject` file you extracted from the game files.
   - This can be located anywhere on your system, it doesn't need to be in your mod folder.
   - This is the model you want to **apply**.

3. **Filter the lists** *(optional)* — use the **Type** and **Package** dropdowns or the search bar to narrow down the items.
   - **Type** — the kind of object (gear, weapon, character, prop, etc.)
   - **Package** — where it comes from (base_game, dlc1, dlc2, dlc3, rogue, etc.)

4. **Pick a SOURCE item** from the left list — this is the model you want to apply.
   - Make sure the `.mgraphobject` file you selected in step 2 matches the highlighted source item.

5. **Pick a TARGET item** from the right list — this is the slot you want to replace.
   - The game will load your source model in place of this item.

6. **Check the centre panel** — review the operation preview for any warnings or errors before proceeding.
   - ⚠ Warnings won't block the swap but are worth reading (e.g. slot mismatch, file already exists).
   - ✗ Errors must be resolved before the swap can run.

7. **Click EXECUTE SWAP** — the tool will copy and rename your source file into the mod folder.
   - A confirmation will appear listing every file that was written.
   - If a file already exists you'll be asked whether to overwrite it.

The tool will copy your source `.mgraphobject` into the mod folder, renamed to match the target slot. The game will then load the source model in place of the target gear.
