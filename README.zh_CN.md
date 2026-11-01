# League-Localization

[Speak English? Click here to view the English introduction.](README.md)

本存储库用于**稳定**修改英雄联盟和云顶之弈客户端的语言，支持“中文（中国）”选项。“稳定”的含义是，在修改客户端语言和下载游戏文件的过程中，保证语言始终是目标语言。

脚本支持修改以下语言配置：（对应拳头客户端中的设置。）
- RIOT客户端
    - GENERAL
        - 语言
- LEAGUE OF LEGENDS
    - 游戏文本语言
- TEAMFIGHT TACTICS
    - 游戏文本语言

对于拳头客户端语言和云顶之弈游戏文本语言，程序只对相应的配置文件作一次修改。对于英雄联盟游戏文本语言，程序循环检测相应的语言配置文件，将其不断改成目标语言，直到联盟客户端启动为止。期间按<ins>Esc</ins>键可以退出提前中止循环。

## 面向用户
1. 中文（中国）语言使用者。
2. 需要频繁切换语言备份游戏文件的人。

## 环境配置
1. 前往[Python官网](https://www.python.org)，下载和安装最新版本的Python。
    - 图文示范可参考[模块：Python安装与全局环境配置](https://zhuanlan.zhihu.com/p/2038292227298996375)一文。
    - 安装前请确保“Add Python.exe to PATH”选项已勾选。
2. 在命令提示符中输入`pip install ruamel.yaml`以安装ruamel.yaml库。
3. 复制以下内容，粘贴到记事本，并进行适当改动，保存到用户文件夹（`C:/Users/[用户名]/`）下的“lol-l10n.ini”文件。
    ```ini
    [paths]
    install_dir = C:/Riot Games
    program_data_dir = C:/ProgramData/Riot Games
    riot_client_config_dir = C:/Users/19250/AppData/Local/Riot Games/Riot Client/Config
    rc_exe = 
    lol_ux_live = 
    lol_ux_pbe = 
    tft_exe_live = 
    tft_exe_pbe = 
    loc_rc = 
    loc_lol_live = 
    loc_lol_pbe = 
    loc_tft_live = 
    loc_tft_pbe = 
    ```

下表给出了各路径的含义以及用户如何去填写这些路径。
<table>
    <thead>
        <tr>
            <th style="text-align:center;">参数名</th>
            <th style="text-align:center;">含义</th>
            <th style="text-align:center;">默认用户操作</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="text-align:center;">install_dir</td>
            <td>拳头游戏的安装目录。</td>
            <td>用户需要更改。</td>
        </tr>
        <tr>
            <td style="text-align:center;">program_data_dir</td>
            <td>程序数据目录。</td>
            <td>一般不需要变动。</td>
        </tr>
        <tr>
            <td style="text-align:center;">riot_client_config_dir</td>
            <td>拳头游戏配置目录。</td>
            <td>一般变动用户名即可。</td>
        </tr>
        <tr>
            <td style="text-align:center;">rc_exe</td>
            <td>拳头客户端可执行文件路径。</td>
            <td>留空即可。程序会根据`install_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">lol_ux_live</td>
            <td>正式服联盟客户端用户体验界面可执行文件路径。</td>
            <td>留空即可。程序会根据`install_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">lol_ux_pbe</td>
            <td>测试服联盟客户端用户体验界面可执行文件路径。</td>
            <td>留空即可。程序会根据`install_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">tft_exe_live</td>
            <td>正式服云顶客户端可执行文件路径。</td>
            <td>留空即可。程序会根据`install_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">tft_exe_pbe</td>
            <td>测试服云顶客户端可执行文件路径。</td>
            <td>留空即可。程序会根据`install_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">loc_rc</td>
            <td>拳头客户端语言配置文件路径。</td>
            <td>留空即可。程序会根据`riot_client_config_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">loc_lol_live</td>
            <td>正式服联盟客户端语言配置文件路径。</td>
            <td>留空即可。程序会根据`program_data_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">loc_lol_pbe</td>
            <td>测试服联盟客户端语言配置文件路径。</td>
            <td>留空即可。程序会根据`program_data_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">loc_tft_live</td>
            <td>正式服云顶客户端语言配置文件路径。</td>
            <td>留空即可。程序会根据`program_data_dir`自动生成该路径。</td>
        </tr>
        <tr>
            <td style="text-align:center;">loc_tft_pbe</td>
            <td>测试服云顶客户端语言配置文件路径。</td>
            <td>留空即可。程序会根据`program_data_dir`自动生成该路径。</td>
        </tr>
    </tbody>
<table>

## 使用方法
请**以管理员身份运行**此程序。下面提供两种方法：
1. 在一个以管理员身份运行的**终端**中用python命令运行此脚本。
    1. 右键Windows图标，选择“<ins>终端（管理员）</ins>”。
    2. 在弹出的“<ins>用户账户控制（UAC）</ins>”窗口中，选择“是”。
    3. 使用`cd`命令切换到存储库目录。
        - 例如，我的存储库的路径是`C:\Users\19250\Documents\GitHub\League-Localization`，则输入`cd "C:\Users\19250\Documents\GitHub\League-Localization"`。
    4. 输入`python 汉化联盟客户端.py`。
        - 可以通过`-l`参数指定目标语言。默认是“中文（中国）”。
        - 可以通过`-c`参数指定配置文件。
        - 完整参数见下面的“参数说明”章节。
2. 在桌面创建一个以管理员身份运行的快捷方式。随后双击该快捷方式即可运行。
    1. 打开命令提示符，输入`where python`。
        - 如果没有任何输出，请先到[Python官网](https://www.python.org)下载和安装Python。
    2. 找到第一行指向的文件，右键选择“创建快捷方式(S)”。
    3. 将快捷方式移动至桌面，重命名为“汉化联盟客户端”。
    4. 右键快捷方式，点击“属性”。
    5. 在“快捷方式”选项卡中，在“目标(T)”的文本后面添加一个半角空格和两个半角双引号。将英雄联盟汉化脚本的路径粘贴到两个双引号之间。
        - 例如，我的`where python`返回的第一行结果是`C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe`。
        - 创建快捷方式后，“快捷方式”选项卡中的“目标”是`C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe`。
        - 英雄联盟汉化脚本的路径是`C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py`。
        - 修改后，“快捷方式”选项卡中的“目标”变成`C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe "C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py"`。
            - 同上一个方法，可以在“目标”中指定语言文化代码。例如，如果想要指定为繁体中文，则“目标”的值应为`C:\Users\19250\AppData\Local\Programs\Python\Python315\python.exe "C:\Users\19250\Documents\GitHub\League-Localization\汉化联盟客户端.py" -l zh_TW`。
            - 如果需要指定其它命令行参数，再次在属性窗口的“快捷方式”选项卡的“目标”中进行修改即可。
    6. 切换到“兼容性”选项卡，勾选“以管理员身份运行此程序”。
    7. 点击“确定”以应用更改并关闭属性窗口。
    8. 双击桌面上的汉化联盟客户端快捷方式。在弹出用户账户控制的提示时，选择“是”。

注：方法一使用的是集成的终端，但是每次启动都需要切换工作目录，操作稍微繁琐一些。方法二可以做到一劳永逸，但是程序的界面是传统的命令提示符界面，没有与终端集成，字体和字号显示可能不太友好。

运行后，用户可以执行以下操作：
1. 输入某个选项对应的编号并按回车键，即可更改语言。
2. 在未启动联盟客户端的情况下更改英雄联盟的语言时，程序会反复修改文件，直到联盟客户端启动或者用户按下<ins>Esc</ins>键中止循环。
3. 输入“0”并按回车键以退出程序。

## 参数说明
<table>
    <thead>
        <tr>
            <th style="text-align:center;">参数简写</th>
            <th style="text-align:center;">参数全称</th>
            <th style="text-align:center;">作用</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="text-align:center;">-l</td>
            <td style="text-align:center;">--locale</td>
            <td>游戏语言。<br>访问<a href="https://developer.riotgames.com/docs/lol#data-dragon_regions">Riot Developer Portal</a>以查看所有支持的语言列表。</td>
        </tr>
        <tr>
            <td style="text-align:center;">-i</td>
            <td style="text-align:center;">--interval</td>
            <td>检测间隔。默认为0.5秒，即每隔0.5秒校正一次语言配置文件。</td>
        </tr>
        <tr>
            <td style="text-align:center;">-c</td>
            <td style="text-align:center;">--config</td>
            <td>适用于本程序的配置文件路径。默认是用户文件夹下的“lol-i10n.ini”。</td>
        </tr>
    </tbody>
<table>

## 其它注意事项
1. 请确保本机未运行其它汉化程序，如加速器的汉化功能。
2. 必须**以管理员身份运行**此程序，以保证程序具有对相关语言配置文件的修改权限。
3. 必须**在运行客户端之前**修改语言，以确保语言变更被及时传送到服务器。
4. 在登出联盟客户端切换账号（例如从测试服切换到正式服或者切换大区）时，有时会出现一种情况：在下载完成目标语言的游戏文件后，点击“游玩”按钮后语言配置会变回默认语言，即使汉化脚本在运行中。这导致刚刚下载好的目标语言的游戏文件被全部删除，转而下载默认语言的游戏文件，之后还得重新下载目标语言的游戏文件。更糟糕的是，这个问题可能会一直重复下去。**如果遇到这种情况，请先退出拳头客户端，然后启动正确的产品再试一次。**
