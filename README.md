# League-Localization

[中文用户？点击此处查看中文介绍。](README.zh_CN.md)

This repository is designed to **steadily** change the language of League of Legends and Teamfight Tactics clients. It supports "Chinese (China)" option. "Steadily" means the program ensures the language is always the target language during the process of downloading game files.

League Localization Program supports changing the following language configuration: (Which corresponds to settings in Riot Client.)
- RIOT CLIENT
    - GENERAL
        - RIOT CLIENT LANGUAGE
- LEAGUE OF LEGENDS
    - GAME TEXT LANGUAGE
- TEAMFIGHT TACTICS
    - GAME TEXT LANGUAGE

For Riot Client language and TFT game text language, the program only makes the change once to the corresponding config files. For LoL game text language, the program detects the corresponding language config file and changes the language to the target one in a loop, until League Client is launched. During the process, users may press <ins>Esc</ins> to cancel the loop in advance.

## Target Users
1. Chinese (**China**) users.
2. People who need to switch languages frequently to backup game files.

## Environment Setup
1. Visit [Python official website](https://www.python.org) to download and install the latest Python release.
    - Refer to [Template: Python Installation and Global Environment Setup](https://zhuanlan.zhihu.com/p/2038292227298996375) for demonstration with pictures.
    - Before installation, please make sure "Add Python.exe to PATH" option is checked.
2. Input `pip install ruamel.yaml` in Command Prompt to install ruamel.yaml library.

## User Manual
Please run this program **as Administrator**. Two methods are provided below:
1. Run this program in a **terminal** run as administrator.
    1. Right-click the Windows icon and select "<ins>Terminal (Administrator)</ins>".
    2. In the "<ins>User Account Control (UAC)</ins>" window that appears, select "Yes".
    3. Use the `cd` command to navigate to the repository directory.
        - For example, the path of my repository is `C:\Users\19250\Documents\GitHub\League-Localization`. Then I should enter `cd "C:\Users\19250\Documents\GitHub\League-Localization"`.
    4. Input `python 汉化联盟客户端.py`。
        - Target language can be specified by `-l` parameter. Refer to the following "Paramater Notes" section to see all parameters.
2. Create a shortcut that run as administrator on desktop. Then, simply double-click this shortcut to run the program.
    1. Open Command Prompt and enter `where python`.
        - If you don't get any output, please visit [Python official website](https://www.python.org) to download and install Python first.
    2. Locale the file shown in the first line of the output. Right-click it and select "Create shortcut".
    3. Move the shortcut to your desktop and rename it to "League Localization Program".
    4. Right-click the shortcut. Select "Properties".
    5. In the "Shortcut" tab, go the "Target" field, add a space after the existing text, and then add two double quotation marks. Paste the file path of League Localization Program between the two double-quotation marks.
        - For example, the first line shown in the output of `where python` is `C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe`.
        - After the shortcut is created, "Target" field in the "Shortcut" tab is `C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe`.
        - The path of League Localization Program is `C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py`.
        - After the change, "Target" field in the "Shortcut" tab becomes `C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe "C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py"`.
            - Same as the above method, users can specify the language code in "Target" field. For example, to specify the language as Traditional Chinese, the value of the "Target" field should be `C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe "C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py" -l zh_TW`.
            - To specify other command line arguments, users can change "Target" field in "Shortcut" page of the Properties window to change it again.
    6. Switch to the "Compatibility" tab and check "Run this program as administrator".
    7. Click "Confirm" to apply the changes and close the "Properties" window.
    8. Double-click the League Localization Program shortcut on the desktop. When User Account Control window appears, select "Yes".

Note: Method One uses the integrated terminal, but requires changing the working directory at each launch, which is a bit cumbersome. Method Two offers a "set it and forget it" solution, but the user interface is the tranditional command prompt interface, where the font style and size may be less friendly.

After launching the program, the user may perform the following operations:
1. Input the number corresponding to an option and press Enter to change the language.
2. When League Client isn't launched and the user selects changing League Client language, the program will repeat changing the file, until League Client is launched or the user has pressed <ins>Esc</ins>.
3. Input "0" and press Enter to exit the program.

## Parameter Notes
<table>
    <thead>
        <tr>
            <th style="text-align:center;">Short Flag</th>
            <th style="text-align:center;">Full Flag</th>
            <th style="text-align:center;">Function</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="text-align:center;">-l</td>
            <td style="text-align:center;">--locale</td>
            <td>Game language.<br>Access <a href="https://developer.riotgames.com/docs/lol#data-dragon_regions">Riot Developer Portal</a>to check the list of all supported languages.</td>
        </tr>
        <tr>
            <td style="text-align:center;">-i</td>
            <td style="text-align:center;">--interval</td>
            <td>Detection interval. 0.5 seconds by default, meaning the language configuration file is corrected every 0.5 seconds.</td>
        </tr>
    </tbody>
<table>

## Other Notes
1. Please ensure no other localization programs are running, e.g. localization function of some accelerators.
2. You must Run this program **As Adminstrator** to make sure the program has the permission to modify the corresponding language configuration files.
3. You must change the language **before running clients** to make sure language changes are sent to server in time.
4. When you sign out League Client and switch to another account (e.g. from PBE to Live or between different regions), sometimes a case happens: after game files in target language are downloaded completely, pressing "Play" button will cause the language configuration to be restored to the default language, despite the running localization program. This causes all of the downloaded game files in target language to be deleted and the client will download game files in default language, and you need to download game files in target language again afterwards. Worse still, this loop may persist. **If you encounter such a situation, please exit Riot Client, then launch the correct product and try again.**
