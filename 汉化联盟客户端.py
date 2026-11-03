import argparse, configparser, msvcrt, os, psutil, time, unicodedata
from wcwidth import wcswidth
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString #使得列表元素强制使用双引号【Force to use double quotes for an element in a list (CommentedSeq)】
from typing import Any, Literal, Optional
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.nodes import ScalarNode

AVAILABLE_LOCALES: list[str] = ["ar_AE", "cs_CZ", "el_GR", "pL_PL", "ro_RO", "hu_HU", "en_GB", "de_DE", "es_ES", "it_IT", "fr_FR", "ja_JP", "ko_KR", "es_MX", "es_AR", "pt_BR", "en_US", "en_AU", "ru_RU", "tr_TR", "ms_MY", "en_PH", "en_SG", "th_TH", "vi_VN", "id_ID", "zh_MY", "zh_CN", "zh_TW"]
RIOT_CLIENT_PATH: str = "C:/Riot Games/Riot Client/RiotClientServices.exe"
RC_LOC_PATH: str = os.path.expanduser("~/AppData/Local/Riot Games/Riot Client/Config/RiotClientSettings.yaml").replace("\\", "/")
LOL_LIVE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.live/league_of_legends.live.product_settings.yaml"
LOL_LIVE_UX_PATH: str = "C:/Riot Games/League of Legends/LeagueClientUx.exe"
LOL_PBE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.pbe/league_of_legends.pbe.product_settings.yaml"
LOL_PBE_UX_PATH: str = "C:/Riot Games/League of Legends (PBE)/LeagueClientUx.exe"
TFT_LIVE_CLIENT_PATH: str = "C:/Riot Games/Teamfight Tactics/Live/TFT/Binaries/Win64/TFTClient-Win64-Shipping.exe"
TFT_PBE_CLIENT_PATH: str = "C:/Riot Games/Teamfight Tactics/PBE/TFT/Binaries/Win64/TFTClient-Win64-Shipping.exe"
TFT_LIVE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/teamfighttactics.live/teamfighttactics.live.product_settings.yaml"
TFT_PBE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/teamfighttactics.pbe/teamfighttactics.pbe.product_settings.yaml"
DEFAULT_CONFIG_PATH: str = os.path.expanduser("~/lol-l10n.ini").replace("\\", "/")
DEFAULT_CONFIG_OBJ: dict[str, dict[str, str]] = {
    "paths": {
        "install_dir": "C:/Riot Games",
        "program_data_dir": "C:/ProgramData/Riot Games",
        "riot_client_config_dir": os.path.expanduser("~/AppData/Local/Riot Games/Riot Client/Config").replace("\\", "/"),
        "rc_exe": "",
        "lol_ux_live": "",
        "lol_ux_pbe": "",
        "tft_exe_live": "",
        "tft_exe_pbe": "",
        "loc_rc": "",
        "loc_lol_live": "",
        "loc_lol_pbe": "",
        "loc_tft_live": "",
        "loc_tft_pbe": ""
    }
}
DEFAULT_CONFIG_STR: str = "\n" + "\n".join([f"[{scope_key}]\n" + "\n".join([f"{key} = {value}" for key, value in scope.items()]) + "\n" for scope_key, scope in DEFAULT_CONFIG_OBJ.items()])

#定义用于排版的函数和变量（Define functions and variables for layout optimization）——其实仅用于语言选项的格式化输出（Actually they're only used for formatted output of language options）
def count_nonASCII(s: str) -> int:
    '''
    统计一个字符串中占用命令行2个宽度单位的字符个数。<br>Count the number of characters that take up 2 width unit in CMD.
    
    :param s: 任意字符串。<br>Any string.
    :type s: str
    :return: 占用2个宽度单位的字符个数。<br>The number of characters that take up 2 width.
    :rtype: int
    '''
    return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])

def rm_ctrl_char(s: str) -> str:
    '''
    移除一个字符串中的所有C0和C1字符。<br>Remove all C0 and C1 characters from a string.
    
    :param s: 原字符串。<br>The original string.
    :type s: str
    :return: 移除终端中显示异常的字符后的字符串。<br>The result string after removing characters that don't display correctly in terminal.
    :rtype: str
    '''
    return "".join(ch for ch in s if unicodedata.category(ch) != "Cc") #该表达式等价于（This expression is equivalent to）`re.sub(r"[\x00-\x1F\x7F-\x9F]", "", s)`

def format_dt(dt: dict[str, list[Any]], print_header: bool = True, print_index: bool = False, start_index: int = 0, header_align: str = "^", align: str = "^", align_replicate_rule: Literal["all", "last"] = "all") -> tuple[str, dict[str, int]]: #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
    '''
    将适用于构建数据框的一个字典转化为列对齐的字符串，用于排版输出。<br>Transform a dictionary into a string where columns are aligned for better page layout.

    :param dt: 要排版的数据字典。<br>A dictionary to transform into a layout-organized string.
    :type dt: dict[str, list[Any]]
    :param print_header: 是否打印表头。默认为真。<br>Whether to print the header. True by default.
    :type print_header: bool
    :param print_index: 是否打印索引列。默认为假。<br>Whether to print the index column. False by default.
    :type print_index: bool
    :param reserve_index: 在打印索引列时，是否输出原始索引。指定为真时则输出原始索引，否则输出从start_index到start_index + len(df) - 1的索引。<br>Whether to print the original indices, when the index column is going to be printed. If it's True, then print the original indices; otherwise, print the index from `start_index` to `start_index + len(df) - 1`.
    :type reserve_index: bool
    :param start_index: 在输出处理后的索引时的起始索引。仅当打印索引列但不输出原始索引时可用。默认值为0。<br>The starting index when the function prints the processed indices. Available only when the index column is going to be printed but not the original indices. Default value is 0.
    :type start_index: int
    :param header_align: 表头对齐方式。可取“<”“^”和“>”三个字符的任意组合。<br>The alignment method of headers, which may be composed of any number of any character among "<", "^" and ">".
        <pre>
        **value**       **description**<br>
        &nbsp;<       左对齐（Left-aligned）<br>
        &nbsp;^       居中对齐（Centered）<br>
        &nbsp;>       右对齐（Right-aligned）
        </pre>
    :type header_align: str
    :param align: 单元格对齐方式。取值规则同header_align参数。<br>The alignment method of cells, whose possible values are the same as those of `header_align` parameter.
    :type align: str
    :param align_replicate_rule: 当表头对齐方式参数和单元格对齐方式参数字符串长度小于列数时，对齐方式的填充规则。共有“all”和“last”两种取值。<br>The rule of filling the aligment method when the alignment method string of headers or cells is less than the number of columns. There're two possible values for this parameter: "all" and "last".
    
        - all: 将整个对齐方式规则循环往复地填充至剩余列。<br>Recursively fill the whole set of alignment methods in the rest of columns.<br>【例】在仅指定前三列单元格的对齐方式分别是左对齐、居中对齐和右对齐的情况下，第四至六列单元格的对齐方式将依次是左对齐、居中对齐和右对齐，往复。<br>[Example] When only the first three columns of cells are specified left-aligned, centered and right-aligned, respectively, the fourth to sixth columns of cells shall be left-aligned, centered and right-aligned, respectively, and so on.
        - last: 将最后一个被指定对齐方式的列的对齐方式填充至剩余列。<br>Fill the alignment method of the last one of the columns specified with alignment methods in the rest of columns.<br>【例】在仅指定前三列单元格的对齐方式分别是左对齐、居中对齐和右对齐的情况下，后面所有列的对齐方式将都是右对齐。<br>[Example] When only the first three columns of cells are specified left-aligned, centered and right-aligned, respectively, all of the subsequent columns of cells shall be right-aligned.
    :type align_replicate_rule: str
    :return: 由格式化字符串和各列宽度字典组成的元组。<br>A tuple composed of the formatted string and each column's width dictionary.
    :rtype: tuple[str, dict[str, str]]
    '''
    #参数预处理（Parameter preprocessing）
    if not (isinstance(dt, dict) and all(map(lambda x: isinstance(x, list), dt.values()))):
        print("数据字典参数错误！请传入一个字典，且字典的值必须是列表。\nParameter ERROR of the data dictionary! Please pass a dictionary whose values are all lists.")
        return ("", {})
    #准备一些常量（Prepare some constants）
    shape: tuple[int, int] = (max(map(len, dt.values())), len(dt)) #表格的行列数（The number of the table's rows and columns）
    dt_index: list[int] = list(range(start_index, shape[0] + start_index)) #新索引允许从`start_index`开始，默认从0开始（New indices allow starting from `start_index`, which is 0 by default）
    index_len: int = 0 if shape[0] == 0 else max(map(lambda x: len(str(x)), dt_index)) #计算索引列的最大字符串宽度（Calculate the max string length of the index column）
    fields: list[str] = list(dt.keys())
    maxLens: dict[str, int] = {} #存储不同列的最大字符串宽度（Stores the max string lengths of different columns）
    for field in fields: #计算每一列的最大字符串宽度（Calculate the max string length of each column）
        maxLens[field] = max(0 if shape[0] == 0 else max(map(lambda x: wcswidth(rm_ctrl_char(str(x))), dt[field])), wcswidth(rm_ctrl_char(str(field)))) + 2
    #确定各列的排列方向（Determine the alignments of all columns）
    if not (isinstance(header_align, str) and isinstance(align, str)): #确保排列方向参数无误（Ensure the alignment parameters are valid）
        print("排列方式参数错误！请传入字符串。\nAlignment parameter ERROR! Please pass a string instead.")
        return ("", maxLens)
    if not all(map(lambda x: x in {"<", "^", ">"}, header_align)) or not all(map(lambda x: x in {"<", "^", ">"}, align)):
        print('排列方式字符串参数错误！排列方式必须是“<”“^”或者“>”中的一个。请修改排列方式字符串参数。\nParameter ERROR of the alignment string! The alignment value must be one of {"<", "^", ">"}. Please change the alignment string parameter.')
        return ("", maxLens)
    if len(header_align) == 0: #指定为空字符串，即默认居中输出（Specifying it as a null string means output centered by default）
        header_alignments: list[str] = ["^"] * shape[1]
    elif len(header_align) == 1:
        header_alignments = [header_align] * shape[1]
    else:
        header_alignments_tmp = list(header_align)
        if len(header_align) < shape[1]: #表头排列规则字符串长度小于数据框列数时，通过排列方式列表补充规则进行补充（When the length of `header_align` is less than the number of the dataframe's columns, supplement the rest of the rules according to `align_replicate_rule`）
            if align_replicate_rule == "last": #仅重复最后一列的排列方式（Only replicate the alignment of the last column）
                header_alignments = header_alignments_tmp + [header_alignments_tmp[-1]] * (shape[1] - len(header_align))
            else:
                if align_replicate_rule != "all":
                    print("排列方式列表补充规则不合法！将默认采用全部填充。\nAlignment list supplement rule illegal! The whole alignment string will be replicated.")
                header_alignments = header_alignments_tmp * (shape[1] // len(header_align)) + header_alignments_tmp[:shape[1] % len(header_align)] #所有排列方式循环补充（Supplement the alignments in a cycle of the whole `header_alignment` string）
        else: #表头排列规则字符串大于等于数据框列数时，取长度等于数据框列数的字符串开头切片（When the length of `header_align` is greater than or equal to the number of the dataframe's columns, get the slice at the beginning of `header_align` whose length equal to the number of the dataframe's columns）
            header_alignments = header_alignments_tmp[:shape[1]]
    if len(align) == 0: #指定为空字符串，即默认居中输出（Specifying it as a null string means output centered by default）
        alignments: list[str] = ["^"] * shape[1]
    elif len(align) == 1:
        alignments = [align] * shape[1]
    else:
        alignments_tmp: list[str] = list(align)
        if len(align) < shape[1]: #数据排列规则字符串长度小于数据框列数时，通过排列方式列表补充规则进行补充（When the length of `align` is less than the number of the dataframe's columns, supplement the rest of the rules according to `align_replicate_rule`）
            if align_replicate_rule == "last": #仅重复最后一列的排列方式（Only replicate the alignment of the last column）
                alignments = alignments_tmp + [alignments_tmp[-1]] * (shape[1] - len(align))
            else:
                if align_replicate_rule != "all":
                    print("排列方式列表补充规则不合法！将默认采用全部填充。\nAlignment list supplement rule illegal! The whole alignment string will be replicated.")
                alignments = alignments_tmp * (shape[1] // len(align)) + alignments_tmp[:shape[1] % len(align)]
        else: #数据排列规则字符串大于等于数据框列数时，取长度等于数据框列数的字符串开头切片（When the length of `align` is greater than or equal to the number of the dataframe's columns, get the slice at the beginning of `header_align` whose length equal to the number of the dataframe's columns）
            alignments = alignments_tmp[:shape[1]]
    #生成结果字符串（Generate the result string）
    result: str = "" #结果字符串初始化（Initialize the result string）
    if print_header: #打印表头（Prints the header）
        if print_index: #打印表头时，如果输出索引，由于表头没有索引，所以用空格代替（Spaces will be printed as the index part of the header）
            result += " " * (index_len + 2)
        for i in range(shape[1]):
            field: str = fields[i]
            tmp: str = "{0:{align}{w}}".format(rm_ctrl_char(str(field)), align = header_alignments[i], w = maxLens[field] - count_nonASCII(field))
            result += tmp
            #print(tmp, end = "")
            if i != shape[1] - 1: #未到行尾时，用两个空格来分割该列和下一列（When the program doesn't reach the end of the line, separate this column and the next column by two spaces）
                result += "  "
                #print("  ", end = "")
        result += "\n"
        #print()
    index: int = start_index
    for i in range(shape[0]):
        if print_index:
            result += "{0:>{w}}".format(index, w = index_len) + "  "
        for j in range(shape[1]):
            field = fields[j]
            cell: str = str(dt[field][i])
            tmp = "{0:{align}{w}}".format(rm_ctrl_char(cell), align = alignments[j], w = maxLens[field] - count_nonASCII(cell))
            result += tmp
            #print(tmp, end = "")
            if j != shape[1] - 1: #未到行尾时，用两个空格来分割该列和下一列（When the program doesn't reach the end of the line, separate this column and the next column by two spaces）
                result += "  "
                #print("  ", end = "")
        if i != shape[0] - 1:
            result += "\n"
        #print() #注意这里的缩进和上一行不同（Note that here the indentation is different from the above line）
        index += 1
    return (result, maxLens)

#定义按键检测函数（Define the key press detection function）
def isKeyPressed(keyCode1: bytes, keyCode2: bytes = b"") -> bool:
    r'''
    检查指定的按键是否在用户**激活当前程序的运行窗口/标签页**时被按下。<br>Check if the specified key is pressed when the user **activates the tab / window of the current program**.
    
    对于简单按键，用户只需要传入第一个字节序列。对于特殊按键，用户需要传入两个不同的字节序列。这是因为`msvcrt.getch`函数一次只能返回一个字节的数据。简单按键的字节数较小，用一个字节便可存下；特殊按键的字节序列较大，需要用两个字节来表示。<br>For a simple key, the user only needs to pass in the first byte sequence. For a special key, the user needs to pass in two different byte sequences. This is because `msvcrt.getch` function can only return one byte of data at a time. The byte sequence of simple keys is smaller and can be stored in one byte; the byte sequence of special keys is larger and requires two bytes.
    
    简单按键的字节序列就是直接以字节形式表示的按键本身，例如：<br>The byte sequence of a simple key is the key itself in byte form, for example:
    - A: (b"a")
    - Space: (b" ")
    
    一些特殊按键的字节序列如下：<br>Some special key byte sequences are as follows:
    - Backspace: (b"\x08")
    - Enter: (b"\r")
    - Esc: (b"\x1b")
    - F1: (b"\x00", b";")
    - F2: (b"\x00", b"<")
    - F3: (b"\x00", b"=")
    - F4: (b"\x00", b">")
    - F5: (b"\x00", b"?")
    - F6: (b"\x00", b"@")
    - F7: (b"\x00", b"A")
    - F8: (b"\x00", b"B")
    - F9: (b"\x00", b"C")
    - F10: (b"\x00", b"D")
    - F11: (b"\x00", b"\x85")
    - F12: (b"\x00", b"\x86")
    - Insert: (b"\xe0", b"R")
    - Delete: (b"\xe0", b"S")
    - Home: (b"\xe0", b"H")
    - End: (b"\xe0", b"P")
    - Page Up: (b"\xe0", b"I")
    - Page Down: (b"\xe0", b"Q")
        
    :param keyCode1: 一个按键对应的第一个字节序列。<br>The first byte sequence of a key.
    :type keyCode1: bytes
    :param keyCode2: 一个按键对应的第二个字节序列。默认是空字节。<br>The second byte sequence of a key. An empty byte by default.
    
        对于简单按键，这个参数不发挥作用。<br>For a simple key, this parameter doesn't make any difference.
    :type keyCode2: bytes
    :return: 指定的按键是否被按下。<br>Whether the specified key is pressed.
    :rtype: bool
    '''
    return bool(msvcrt.kbhit()) and msvcrt.getch() == keyCode1 and (keyCode1 != b"\xe0" and keyCode1 != b"\000" or msvcrt.getch() == keyCode2)

#定义语言管理相关类和过程（Define language management related class and processes）
class LoLLocaleManager:
    #定义语言设置相关常量（Define language settings related constants）
    LANGUAGE_DDRAGON: dict[str, dict[str, str]] = {
        "ar_AE": {
            "desc_en": "Arabic (United Arab Emirates)",
            "desc_zh": "阿拉伯语（阿拉伯联合酋长国）",
            "desc_local": "العربية (الإمارات العربية المتحدة)",
            "Available CDragon Data Patches": "9.20～10.1, 13.20+"
        },
        "cs_CZ": {
            "desc_en": "Czech (Czech Republic)",
            "desc_zh": "捷克语（捷克共和国）",
            "desc_local": "Čeština (Česká republika)",
            "Available CDragon Data Patches": "7.1+"
        },
        "el_GR": {
            "desc_en": "Greek (Greece)",
            "desc_zh": "希腊语（希腊）",
            "desc_local": "Ελληνικά (Ελλάδα)",
            "Available CDragon Data Patches": "7.1+"
        },
        "pl_PL": {
            "desc_en": "Polish (Poland)",
            "desc_zh": "波兰语（波兰）",
            "desc_local": "Polski (Polska)",
            "Available CDragon Data Patches": "7.1+"
        },
        "ro_RO": {
            "desc_en": "Romanian (Romania)",
            "desc_zh": "罗马尼亚语（罗马尼亚）",
            "desc_local": "Română (România)",
            "Available CDragon Data Patches": "7.1+"
        },
        "hu_HU": {
            "desc_en": "Hungarian (Hungary)",
            "desc_zh": "匈牙利语（匈牙利）",
            "desc_local": "Magyar (Magyarország)",
            "Available CDragon Data Patches": "7.1+"
        },
        "en_GB": {
            "desc_en": "English (United Kingdom)",
            "desc_zh": "英语（英国）",
            "desc_local": "English (United Kingdom)",
            "Available CDragon Data Patches": "7.1+"
        },
        "de_DE": {
            "desc_en": "German (Germany)",
            "desc_zh": "德语（德国）",
            "desc_local": "Deutsch (Deutschland)",
            "Available CDragon Data Patches": "7.1+"
        },
        "es_ES": {
            "desc_en": "Spanish (Spain)",
            "desc_zh": "西班牙语（西班牙）",
            "desc_local": "Español (España)",
            "Available CDragon Data Patches": "7.1+"
        },
        "it_IT": {
            "desc_en": "Italian (Italy)",
            "desc_zh": "意大利语（意大利）",
            "desc_local": "Italiano (Italia)",
            "Available CDragon Data Patches": "7.1+"
        },
        "fr_FR": {
            "desc_en": "French (France)",
            "desc_zh": "法语（法国）",
            "desc_local": "Français (France)",
            "Available CDragon Data Patches": "7.1+"
        },
        "ja_JP": {
            "desc_en": "Japanese (Japan)",
            "desc_zh": "日语（日本）",
            "desc_local": "日本語 (日本)",
            "Available CDragon Data Patches": "7.1+"
        },
        "ko_KR": {
            "desc_en": "Korean (Korea)",
            "desc_zh": "朝鲜语（韩国）",
            "desc_local": "한국어 (대한민국)",
            "Available CDragon Data Patches": "9.7+"
        },
        "es_MX": {
            "desc_en": "Spanish (Mexico)",
            "desc_zh": "西班牙语（墨西哥）",
            "desc_local": "Español (México)",
            "Available CDragon Data Patches": "7.1+"
        },
        "es_AR": {
            "desc_en": "Spanish (Argentina)",
            "desc_zh": "西班牙语（阿根廷）",
            "desc_local": "Español (Argentina)",
            "Available CDragon Data Patches": "9.7+"
        },
        "pt_BR": {
            "desc_en": "Portuguese (Brazil)",
            "desc_zh": "葡萄牙语（巴西）",
            "desc_local": "Português (Brasil)",
            "Available CDragon Data Patches": "7.1+"
        },
        "en_US": {
            "desc_en": "English (United States)",
            "desc_zh": "英语（美国）",
            "desc_local": "English (United States)",
            "Available CDragon Data Patches": "7.1+"
        },
        "en_AU": {
            "desc_en": "English (Australia)",
            "desc_zh": "英语（澳大利亚）",
            "desc_local": "English (Australia)",
            "Available CDragon Data Patches": "7.1+"
        },
        "ru_RU": {
            "desc_en": "Russian (Russia)",
            "desc_zh": "俄语（俄罗斯）",
            "desc_local": "Русский (Россия)",
            "Available CDragon Data Patches": "7.1+"
        },
        "tr_TR": {
            "desc_en": "Turkish (Turkey)",
            "desc_zh": "土耳其语（土耳其）",
            "desc_local": "Türkçe (Türkiye)",
            "Available CDragon Data Patches": "7.1+"
        },
        "ms_MY": {
            "desc_en": "Malay (Malaysia)",
            "desc_zh": "马来语（马来西亚）",
            "desc_local": "Bahasa Melayu (Malaysia)",
            "Available CDragon Data Patches": ""
        },
        "en_PH": {
            "desc_en": "English (Republic of the Philippines)",
            "desc_zh": "英语（菲律宾共和国）",
            "desc_local": "English (Pilipinas)",
            "Available CDragon Data Patches": "10.5+"
        },
        "en_SG": {
            "desc_en": "English (Singapore)",
            "desc_zh": "英语（新加坡）",
            "desc_local": "English (Singapore)",
            "Available CDragon Data Patches": "10.5+"
        },
        "th_TH": {
            "desc_en": "Thai (Thailand)",
            "desc_zh": "泰语（泰国）",
            "desc_local": "ภาษาไทย (ประเทศไทย)",
            "Available CDragon Data Patches": "9.7+"
        },
        "vn_VN": {
            "desc_en": "Vietnamese (Viet Nam)",
            "desc_zh": "越南语（越南）",
            "desc_local": "Tiếng Việt (Việt Nam)",
            "Available CDragon Data Patches": "9.7～13.9"
        },
        "vi_VN": {
            "desc_en": "Vietnamese (Viet Nam)",
            "desc_zh": "越南语（越南）",
            "desc_local": "Tiếng Việt (Việt Nam)",
            "Available CDragon Data Patches": "12.17+"
        },
        "id_ID": {
            "desc_en": "Indonesian (Indonesia)",
            "desc_zh": "印度尼西亚语（印度尼西亚）",
            "desc_local": "Bahasa Indonesia (Indonesia)",
            "Available CDragon Data Patches": "15.5+"
        },
        "zh_MY": {
            "desc_en": "Chinese (Malaysia)",
            "desc_zh": "中文（马来西亚）",
            "desc_local": "中文 (马来西亚)",
            "Available CDragon Data Patches": "10.5+"
        },
        "zh_CN": {
            "desc_en": "Chinese (China)",
            "desc_zh": "中文（中国）",
            "desc_local": "中文 (中国)",
            "Available CDragon Data Patches": "9.7+"
        },
        "zh_TW": {
            "desc_en": "Chinese (Taiwan)",
            "desc_zh": "中文（台湾）",
            "desc_local": "中文 (台灣)",
            "Available CDragon Data Patches": "9.7+"
        }
    }
    LANGUAGE_DICT: dict[str, list[int | str]] = {
        "No.": list(range(1, len(LANGUAGE_DDRAGON) + 1)),
        "CODE": list(LANGUAGE_DDRAGON.keys()),
        "LANGUAGE": list(map(lambda x: x["desc_local"], LANGUAGE_DDRAGON.values())),
        "Available CDragon Data Patches": list(map(lambda x: x["Available CDragon Data Patches"], LANGUAGE_DDRAGON.values()))
    }
    
    def __init__(self, locale: str = "zh_CN", interval: float = 0.5, config_path: str = DEFAULT_CONFIG_PATH) -> None:
        '''
        构建一个语言管理器对象。<br>Construct a `LoLLocaleManager` object.
        
        :param locale: 目标语言文化代码。默认为中文（中国）。<br>Target language code. Chinese (China) by default.
        :type locale: str
        :param interval: 循环修改模式下检测yaml文件变更的间隔（单位：秒）。默认为0.5秒。<br>The time interval to detect whether the yaml file is changed under Loop Edit Mode, in seconds. 0.5 seconds by default.
        :type interval: float
        '''
        #可设置的属性（Configurable attributes）
        self.locale: str = locale #目标语言文化代码（Target language code）
        self.interval: float = interval #循环修改时的读取间隔（Time interval between two reads in Loop Edit mode）
        self.config_path: str = config_path #配置文件路径（Path of configuration file）
        #其它公开属性（Other public attributes）
        self.paths_ready: dict[str, bool] = {"rcPath": False, "lolUxPath_live": False, "lolUxPath_pbe": False, "tftClientPath_live": False, "tftClientPath_pbe": False, "locPath_rc": False, "locPath_lol_ux_live": False, "locPath_lol_ux_pbe": False, "locPath_tft_live": False, "locPath_tft_pbe": False} #各路径是否存在（Whether each path exists）
        #私密属性（Private attributes）
        self._yaml: YAML = YAML() #初始化YAML读取引擎（Initialize YAML reading engine）
        #自动生成的属性（Automatically generated attributes）
        self.init_config_data()
        self.init_loc_data()
    
    def init_config_data(self) -> None:
        '''
        初始化程序配置数据。<br>Initialize program configuration data.
        '''
        self.config: configparser.ConfigParser = self.load_config() #配置文件对象（Configuration file object）
        if not self.verify_config(self.config):
            raise TypeError("Invalid program config data. Please check the format.")
        paths: dict[str, str] = self.derive_paths(self.config)
        self.rcPath: str = paths["rcPath"] #拳头客户端的可执行文件路径（Path of Riot Client executable）
        self.lolUxPath_live: str = paths["lolUxPath_live"] #正式服联盟客户端用户体验界面可执行文件路径（Path of Live League Client User Experience executable file）
        self.lolUxPath_pbe: str = paths["lolUxPath_pbe"] #测试服联盟客户端用户体验界面可执行文件路径（Path of PBE League Client User Experience executable file）
        self.tftClientPath_live: str = paths["tftClientPath_live"] #正式服云顶客户端可执行文件路径（Path of Live TFT Client executable files）
        self.tftClientPath_pbe: str = paths["tftClientPath_pbe"] #测试服云顶客户端可执行文件路径（Path of PBE TFT Client executable files）
        self.locPath_rc: str = paths["locPath_rc"] #拳头客户端语言配置文件路径（Path of Riot Client language configuration file）
        self.locPath_lol_ux_live: str = paths["locPath_lol_ux_live"] #正式服联盟客户端语言配置文件的路径（Path of Live League Client language configuration file）
        self.locPath_lol_ux_pbe: str = paths["locPath_lol_ux_pbe"] #测试服联盟客户端语言配置文件的路径（Path of PBE League Client language configuration file）
        self.locPath_tft_live: str = paths["locPath_tft_live"] #正式服云顶客户端语言配置文件的路径（Path of Live TFT Client language configuration file）
        self.locPath_tft_pbe: str = paths["locPath_tft_pbe"] #测试服云顶客户端语言配置文件的路径（Path of PBE TFT Client language configuration file）
    
    def init_loc_data(self) -> None:
        '''
        初始化语言配置数据。<br>Initialize language configuration data.
        '''
        self.rc_loc_data: CommentedMap = CommentedMap() #初始化拳头客户端语言配置数据（Initialize Riot Client language configuration data）
        self.gt_loc_data: CommentedMap = CommentedMap() #初始化游戏文本语言配置数据（Initialize game text language configuration data）
        self.error_count: int = 0 #错误次数（Number of errors）
    
    #定义程序配置文件操作方法（Define program config file operation methods）
    def load_config(self, config_path: Optional[str] = None) -> configparser.ConfigParser: #不能在方法内部直接令`self.config = cfg`而将函数返回值设置为空，因为这个函数还用于配置的校验，那时是不期望直接设置属性的（We can't add `self.config = cfg` to the end of the function and set the return value as None, because this function is also used for config verification, when it's not intended to assign the config attribute）
        '''
        读取配置文件。<br>Load configuration file.
        
        :param config_path: 配置文件路径。如果未指定，则使用对象中的配置文件路径。<br>Path of configuration file. If it's not specified, then the config file path of the object will be used.
        :type config_path: str
        '''
        if config_path is None:
            config_path = self.config_path
        cfg: configparser.ConfigParser = configparser.ConfigParser()
        if os.path.exists(config_path) and os.path.isfile(config_path):
            cfg.read(config_path, encoding = "utf-8")
        else:
            cfg.read_string(DEFAULT_CONFIG_STR)
            with open(config_path, "w", encoding = "utf-8") as fp:
                cfg.write(fp)
        if not cfg.has_section("paths"):
            cfg.add_section("paths")
        for key, default_value in DEFAULT_CONFIG_OBJ["paths"].items():
            if not cfg.has_option("paths", key):
                cfg.set("paths", key, default_value)
        return cfg
    
    def save_config(self) -> None:
        '''
        保存配置文件。<br>Save configuration file.
        '''
        with open(self.config_path, "w", encoding = "utf-8") as fp:
            self.config.write(fp)
    
    @staticmethod
    def derive_paths(cfg: configparser.ConfigParser) -> dict[str, str]:
        '''
        从配置文件对象中派生出各路径。<br>Derive paths from configuration file object.
        
        通过下面的目录派生其所包含的文件的路径：<br>Derive the paths of files contained in the following directories:
        - install_dir: 拳头游戏安装目录。<br>Riot games installation directory.
            - rc_exe: 拳头客户端可执行文件路径。<br>Riot Client executable path.
            - lol_ux_live: 正式服联盟客户端用户体验界面可执行文件路径。<br>Live League Client User Experience executable file path.
            - lol_ux_pbe: 测试服联盟客户端用户体验界面可执行文件路径。<br>PBE League Client User Experience executable file path.
            - tft_exe_live: 正式服云顶客户端可执行文件路径。<br>Live TFT Client executable path.
            - tft_exe_pbe: 测试服云顶客户端可执行文件路径。<br>PBE TFT Client executable path.
        - program_data_dir: 拳头游戏程序数据目录。<br>Riot games program data directory.
            - loc_rc: 拳头客户端语言配置文件路径。<br>Riot Client language configuration file path.
        - riot_client_config_dir: 拳头客户端配置目录。<br>Riot Client configuration directory.
            - loc_lol_live: 正式服联盟客户端语言配置文件路径。<br>Live League Client language configuration file path.
            - loc_lol_pbe: 测试服联盟客户端语言配置文件路径。<br>PBE League Client language configuration file path.
            - loc_tft_live: 正式服云顶客户端语言配置文件路径。<br>Live TFT Client language configuration file path.
            - loc_tft_pbe: 测试服云顶客户端语言配置文件路径。<br>PBE TFT Client language configuration file path.
        
        :param cfg: 配置文件对象。<br>Configuration file object.
        :type cfg: configparser.ConfigParser
        :return: 各路径的字典。<br>Dictionary of paths.
        :rtype: dict[str, str]
        '''
        def norm_path(p: str) -> str:
            '''
            标准化路径写法。<br>Normalize path writing.
            
            :param p: 待处理的路径。<br>Path to be processed.
            :type p: str
            :return: 标准化后的路径。<br>Normalized path.
            :rtype: str
            '''
            return os.path.expanduser(p).replace("\\", "/").rstrip("/")
        
        install_dir: str = norm_path(cfg.get("paths", "install_dir"))
        pd_dir: str = norm_path(cfg.get("paths", "program_data_dir"))
        rc_cfg_dir: str = norm_path(cfg.get("paths", "riot_client_config_dir"))

        derived: dict[str, str] = {
            "rcPath": f"{install_dir}/Riot Client/RiotClientServices.exe",
            "lolUxPath_live": f"{install_dir}/League of Legends/LeagueClientUx.exe",
            "lolUxPath_pbe": f"{install_dir}/League of Legends (PBE)/LeagueClientUx.exe",
            "tftClientPath_live": f"{install_dir}/Teamfight Tactics/Live/TFT/Binaries/Win64/TFTClient-Win64-Shipping.exe",
            "tftClientPath_pbe": f"{install_dir}/Teamfight Tactics/PBE/TFT/Binaries/Win64/TFTClient-Win64-Shipping.exe",
            "locPath_rc": f"{rc_cfg_dir}/RiotClientSettings.yaml",
            "locPath_lol_ux_live": f"{pd_dir}/Metadata/league_of_legends.live/league_of_legends.live.product_settings.yaml",
            "locPath_lol_ux_pbe": f"{pd_dir}/Metadata/league_of_legends.pbe/league_of_legends.pbe.product_settings.yaml",
            "locPath_tft_live": f"{pd_dir}/Metadata/teamfighttactics.live/teamfighttactics.live.product_settings.yaml",
            "locPath_tft_pbe": f"{pd_dir}/Metadata/teamfighttactics.pbe/teamfighttactics.pbe.product_settings.yaml",
        }
        override_map: dict[str, str] = {
            "rcPath": "rc_exe",
            "lolUxPath_live": "lol_ux_live",
            "lolUxPath_pbe": "lol_ux_pbe",
            "tftClientPath_live": "tft_exe_live",
            "tftClientPath_pbe":  "tft_exe_pbe",
            "locPath_rc": "loc_rc",
            "locPath_lol_ux_live": "loc_lol_live",
            "locPath_lol_ux_pbe": "loc_lol_pbe",
            "locPath_tft_live": "loc_tft_live",
            "locPath_tft_pbe": "loc_tft_pbe",
        } #存储语言管理器中的路径属性成员的名称和配置文件中的键名的映射关系（Store the mapping between the names of path attributes in the locale manager and the key names in the configuration file）
        for attr, key in override_map.items():
            v: str = cfg.get("paths", key, fallback = "").strip()
            if bool(v): #如果配置中单独指定过个别文件的位置，则使用该位置（If some specific file has unqiue location in the config, use this location）
                derived[attr] = norm_path(v)
        return derived
    
    @staticmethod
    def verify_config(cfg: configparser.ConfigParser) -> bool:
        '''
        检验程序配置是否正确。<br>Verify whether the program config is correct.
        
        :param cfg: 待检验的程序配置。<br>A program config to verify.
        :type cfg: configparser.ConfigParser
        :return: 程序配置格式的正确性。<br>Correctness of the program config format.
        :rtype: bool
        '''
        return isinstance(cfg, configparser.ConfigParser) and cfg.has_section("paths") and cfg.has_option("paths", "install_dir") and cfg.has_option("paths", "program_data_dir") and cfg.has_option("paths", "riot_client_config_dir")
    
    def set_locale(self, locale: Optional[int | str] = None) -> None:
        '''
        设置目标语言文化代码。<br>Set the target language code.
        
        :param locale: 目标语言文化代码或编号。如果不指定，则在方法内部询问。<br>Target language code or its corresponding number. If it's not specified, the method will ask the user to specify it.
        
            编号可通过本类的`LANGUAGE_DICT`常量查询。<br>The number can be accessed by `LANGUAGE_DICT` constant of this class.
        :type locale: int | str
        '''
        useParam: bool = False
        if locale is not None:
            if isinstance(locale, int):
                if locale > 1 and locale <= len(self.LANGUAGE_DDRAGON):
                    self.locale = list(self.LANGUAGE_DDRAGON.keys())[locale - 1]
                    useParam = True
                else:
                    print("下标越界。将转为手动输入。\nIndex out of bounds. You'll be asked to manually input it.")
            else:
                if locale in self.LANGUAGE_DDRAGON:
                    self.locale = locale
                    useParam = True
                else:
                    print("语言文化代码无效。将转为手动输入。\nInvalid language code. You'll be asked to manually input it.")
        if not useParam:
            new_locale: str = self.locale
            print('请选择目标语言：（输入“0”以取消更改。）\nPlease select the target language: (Submit "0" to cancel the change.)')
            print(format_dt(self.LANGUAGE_DICT)[0])
            while True:
                language_option: str = input()
                if language_option == "":
                    new_locale = "zh_CN"
                    break
                elif language_option[0] == "0":
                    break
                elif language_option in set(map(str, self.LANGUAGE_DICT["No."])):
                    new_locale = list(self.LANGUAGE_DDRAGON.keys())[int(language_option) - 1]
                    break
                else:
                    print("语言选项输入错误！请重新输入。\nERROR input of language option! Please try again.")
            if new_locale != self.locale:
                self.locale = new_locale
                print("目标语言已设置为%s。\nTarget language has been set to %s." %(self.LANGUAGE_DDRAGON[new_locale]["desc_zh"], self.LANGUAGE_DDRAGON[new_locale]["desc_en"]))
    
    def set_interval(self, interval: Optional[float] = None) -> None:
        '''
        设置循环间隔。<br>Set the loop interval.
        
        :param interval: 循环间隔，单位是秒。如果不指定，则在方法内部询问。<br>Loop interval, in seconds. If it's not specified, the method will ask the user to specify it.
        :type interval: float
        '''
        useParam: bool = interval is not None
        if useParam:
            self.interval = interval
        else:
            new_interval: float = self.interval
            print('请设置新的循环间隔，单位是秒。输入“0”以取消更改。\nPlease set the new loop interval, in seconds. Submit "0" to cancel the change.')
            while True:
                new_interval_str: str = input()
                if new_interval_str == "":
                    continue
                elif new_interval_str == "0":
                    break
                else:
                    try:
                        new_interval = float(new_interval_str)
                    except ValueError:
                        print("请输入一个数字。\nPlease input a number.")
                    else:
                        break
            if new_interval != self.interval:
                self.interval = new_interval
                print(f"循环间隔已设置为{new_interval}秒。\nLoop interval has been set to {new_interval} seconds.")

    def set_config(self, config_path: Optional[str] = None) -> None:
        '''
        设置配置文件路径。<br>Set the config file path.
        
        :param config_path: 通过方法的参数传入的配置文件路径。如果不指定，则在方法内部询问。<br>The config file path passed through the method parameter. If it's not specified, the method will ask the user to specify it.
        :type config_path: str
        '''
        useParam: bool = False
        if config_path is not None:
            try:
                self.load_config(config_path = config_path)
            except:
                print("读取配置文件的过程出现了一个异常。将转为手动输入。\nAn error occurred during the process of reading the config file. You'll be asked to manually input it.")
            else:
                self.config_path = config_path
                self.init_config_data()
                useParam = True
        if not useParam:
            print('请输入配置文件路径：（输入“0”以取消更改。）\nPlease input the path of the config file: (Submit "0" to cancel the change.)\n当前配置文件（Current config file）： ' + self.config_path)
            while True:
                path: str = input()
                if path == "":
                    continue
                elif path == "0":
                    break
                else:
                    if not os.path.exists(path):
                        print("路径不存在。请重新输入。\nPath not found. Please try again.")
                    elif not os.path.isfile(path):
                        print("请输入一个文件。\nPlease input a file.")
                    else:
                        try:
                            self.load_config(config_path = path)
                        except:
                            print("读取配置文件的过程出现了一个异常。请切换文件后再试。\nAn error occurred during the process of reading the config file. Please change another file and try again.")
                        else:
                            self.config_path = path
                            self.init_config_data()
                            if self.verify_config(self.config):
                                break
                            else:
                                print("配置文件格式有误。请调整后再试一次。\nInvalid config file format. Please adjust it and try again.")
    
    #定义YAML引擎参数调整方法（Define a YAML engine parameter adjustment method）
    def set_yaml_params(self, mapping: int = 4, sequence: int = 4, offset: int = 2, preserve_quotes: bool = True, width: int = 4096) -> None:
        '''
        调整YAML引擎的参数。<br>Adjust parameters of the YAML engine.
        
        :param mapping: 每个键值对的值前空格与键前空格之间的差值。默认为4个空格。<br>The difference of the number of spaces between in front of the key and in front of the value. 4 spaces by default.
        :type mapping: int
        :param sequence: 列表项的缩进空格数量。默认为4个空格。<br>The number of spaces used for indentation of a list item. 4 by default.
        :type sequence: int
        :param offset: 键值对中列表项的偏移空格数量。默认为2个空格。<br>The number of offset spaces ahead of a list item in a key-value pair. 2 by default.
        :type offset: int
        :param preserve_quotes: 是否保留字符串两侧的双引号。默认为真。<br>Whether to reserve the double quotes enclosing a string. True by default.
        :type preserve_quotes: bool
        :param width: 单行最大字符数量。默认为4096个字符。<br>The maximum number of characters in a single line. 4096 characters by default.
        :type width: int
        '''
        self._yaml.indent(mapping = mapping, sequence = sequence, offset = offset)
        self._yaml.preserve_quotes = preserve_quotes
        self._yaml.width = width
        def represent_none(self: RoundTripRepresenter, data: None) -> ScalarNode:
            '''
            YAML引擎的空值处理策略。<br>Empty value handling strategy of YAML engine.
            '''
            return self.represent_scalar("tag:yaml.org,2002:null", "null")
        self._yaml.representer.add_representer(type(None), represent_none)
    
    #定义参数检查方法族（Define member checking method family）
    def check_rcPath(self) -> bool:
        '''
        检查拳头客户端的可执行文件路径。如果路径不存在，则要求用户修改。<br>Check the path of Riot Client executable. If it doesn't exist, then this function asks the user to change it.
        
        :return: 拳头客户端的可执行文件是否准备就绪。<br>Whether Riot Client executable is ready.
        :rtype: bool
        '''
        if os.path.exists(self.rcPath):
            self.paths_ready["rcPath"] = True
        else:
            print(f"请指定拳头客户端的可执行文件路径。例如：\nPlease specify an existing path of Riot Client executable. Example:\n{self.rcPath}")
            while True:
                rcPath: str = input()
                if rcPath == "":
                    pass
                elif rcPath[0] == "0":
                    self.paths_ready["rcPath"] = False
                    break
                elif not os.path.exists(rcPath):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(rcPath):
                    print("请输入一个文件。\nPlease input a file.")
                elif not os.path.basename(rcPath) == "RiotClientServices.exe":
                    print("请输入拳头客户端的可执行文件路径。\nPlease input a path of Riot Client executable.")
                else:
                    self.rcPath = rcPath.replace("\\", "/")
                    self.paths_ready["rcPath"] = True
                    self.config.set("paths", "rc_exe", self.rcPath)
                    self.save_config()
                    break
        return self.paths_ready["rcPath"]
    
    def check_lolUxPath(self, patchline: str) -> bool:
        '''
        检查英雄联盟客户端用户体验界面可执行文件的路径。如果路径不存在，则要求用户修改。<br>Check the path of League Client User Experience executable. If it doesn't exist, then this function asks the user to change it.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 英雄联盟客户端用户体验界面可执行文件是否准备就绪。<br>Whether League Client User Experience executable is ready.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        uxPath: str = self.lolUxPath_live if patchline == "live" else self.lolUxPath_pbe
        uxPath_key: str = "lolUxPath_live" if patchline == "live" else "lolUxPath_pbe"
        patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
        patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
        #函数主体（Function body）
        if os.path.exists(uxPath):
            self.paths_ready[uxPath_key] = True
        else:
            print(f"请指定{patchline_loc_zh}英雄联盟客户端用户体验界面的可执行文件路径。例如：\nPlease specify an existing path of {patchline_loc_en} League Client User Experience executable. Example:\n{uxPath}")
            while True:
                uxPath_tmp: str = input()
                if uxPath_tmp == "":
                    pass
                elif uxPath_tmp[0] == "0":
                    self.paths_ready[uxPath_key] = False
                    break
                elif not os.path.exists(uxPath_tmp):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(uxPath_tmp):
                    print("请输入一个文件。\nPlease input a file.")
                elif not os.path.basename(uxPath_tmp) == "LeagueClientUx.exe":
                    print(f"请输入{patchline_loc_zh}英雄联盟客户端用户体验界面的可执行文件路径。\nPlease input a path of {patchline_loc_en} League Client User Experience executable.")
                else:
                    if patchline == "live":
                        self.lolUxPath_live = uxPath_tmp.replace("\\", "/")
                        self.config.set("paths", "lol_ux_live", self.lolUxPath_live)
                    else:
                        self.lolUxPath_pbe = uxPath_tmp.replace("\\", "/")
                        self.config.set("paths", "lol_ux_pbe", self.lolUxPath_pbe)
                    self.paths_ready[uxPath_key] = True
                    self.save_config()
                    break
        return self.paths_ready[uxPath_key]
    
    def check_tftClientPath(self, patchline: str) -> bool:
        '''
        检查云顶之弈客户端可执行文件的路径。如果路径不存在，则要求用户修改。<br>Check the path of TFT Client executable. If it doesn't exist, then this function asks the user to change it.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 云顶之弈客户端可执行文件是否准备就绪。<br>Whether TFT Client executable is ready.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        uxPath: str = self.tftClientPath_live if patchline == "live" else self.tftClientPath_pbe
        uxPath_key: str = "tftClientPath_live" if patchline == "live" else "tftClientPath_pbe"
        patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
        patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
        #函数主体（Function body）
        if os.path.exists(uxPath):
            self.paths_ready[uxPath_key] = True
        else:
            print(f"请指定{patchline_loc_zh}云顶之弈客户端的可执行文件路径。例如：\nPlease specify an existing path of {patchline_loc_en} TFT Client executable. Example:\n{uxPath}")
            while True:
                uxPath_tmp: str = input()
                if uxPath_tmp == "":
                    pass
                elif uxPath_tmp[0] == "0":
                    self.paths_ready[uxPath_key] = False
                    break
                elif not os.path.exists(uxPath_tmp):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(uxPath_tmp):
                    print("请输入一个文件。\nPlease input a file.")
                elif not os.path.basename(uxPath_tmp) == "TFTClient-Win64-Shipping.exe":
                    print(f"请输入{patchline_loc_zh}云顶之弈客户端的可执行文件路径。\nPlease input a path of {patchline_loc_en} TFT Client executable.")
                else:
                    if patchline == "live":
                        self.tftClientPath_live = uxPath_tmp.replace("\\", "/")
                        self.config.set("paths", "tft_exe_live", self.tftClientPath_live)
                    else:
                        self.tftClientPath_pbe = uxPath_tmp.replace("\\", "/")
                        self.config.set("paths", "tft_exe_pbe", self.tftClientPath_pbe)
                    self.paths_ready[uxPath_key] = True
                    self.save_config()
                    break
        return self.paths_ready[uxPath_key]
    
    def check_locPath_rc(self) -> bool:
        '''
        检查拳头客户端的语言配置文件路径。如果路径不存在，则要求用户修改。<br>Check the path of Riot Client language configuration file. If it doesn't exist, then this function asks the user to change it.
        
        :return: 拳头客户端的语言配置文件是否准备就绪。<br>Whether Riot Client language configuration file is ready.
        :rtype: bool
        '''
        if os.path.exists(self.locPath_rc):
            self.paths_ready["locPath_rc"] = True
        else:
            print(f"请指定拳头客户端的语言配置文件路径。例如：\nPlease specify an existing path of Riot Client language configuration file. Example:\n{self.locPath_rc}")
            while True:
                locPath_rc: str = input()
                if locPath_rc == "":
                    pass
                elif locPath_rc[0] == "0":
                    self.paths_ready["locPath_rc"] = False
                    break
                elif not os.path.exists(locPath_rc):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(locPath_rc):
                    print("请输入一个文件。\nPlease input a file.")
                elif not os.path.basename(locPath_rc) == "RiotClientSettings.yaml":
                    print("请输入拳头客户端的语言配置文件路径。\nPlease input a path of Riot Client language configuration file.")
                else:
                    self.locPath_rc = locPath_rc.replace("\\", "/")
                    self.paths_ready["locPath_rc"] = True
                    self.config.set("paths", "loc_rc", self.locPath_rc)
                    self.save_config()
                    break
        return self.paths_ready["locPath_rc"]
    
    def check_locPath_gt(self, product: str, patchline: str) -> bool:
        '''
        检查联盟客户端或云顶客户端的游戏文本语言配置文件路径。如果路径不存在，则要求用户修改。<br>Check the path of the game text language configuration file of League Client or TFT Client. If it doesn't exist, then this function asks the user to change it.
        
        :param product: 游戏产品。<br>Game product.
        
            - LoL: 英雄联盟
            - TFT: 云顶之弈
        :type product: Literal["LoL", "TFT"]
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 联盟客户端或云顶客户端的游戏文本语言配置文件是否准备就绪。<br>Whether the game text language configuration file of League Client or TFT Client is ready.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if product != "TFT":
            product = "LoL"
        if patchline != "live":
            patchline = "pbe"
        if product == "TFT":
            locPath_ux: str = self.locPath_tft_live if patchline == "live" else self.locPath_tft_pbe
            locPath_ux_key: str = "locPath_tft_live" if patchline == "live" else "locPath_tft_pbe"
        else:
            locPath_ux = self.locPath_lol_ux_live if patchline == "live" else self.locPath_lol_ux_pbe
            locPath_ux_key = "locPath_lol_ux_live" if patchline == "live" else "locPath_lol_ux_pbe"
        client_loc_zh: str = "联盟客户端" if product == "LoL" else "云顶客户端"
        client_loc_en: str = "League Client" if product == "LoL" else "TFT Client"
        product_name: str = "league_of_legends" if product == "LoL" else "teamfighttactics"
        patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
        patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
        #函数主体（Function body）
        if os.path.exists(locPath_ux):
            self.paths_ready[locPath_ux_key] = True
        else:
            print(f"请指定{patchline_loc_zh}{client_loc_zh}的语言配置文件路径。例如：\nPlease specify an existing path of {patchline_loc_en} {client_loc_en} language configuration file. Example:\n{locPath_ux}")
            while True:
                locPath_ux_tmp: str = input()
                if locPath_ux_tmp == "":
                    pass
                elif locPath_ux_tmp[0] == "0":
                    self.paths_ready[locPath_ux_key] = False
                    break
                elif not os.path.exists(locPath_ux_tmp):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(locPath_ux_tmp):
                    print("请输入一个文件。\nPlease input a file.")
                elif not os.path.basename(locPath_ux_tmp) == f"{product_name}.{patchline}.product_settings.yaml":
                    print(f"请输入{patchline_loc_zh}{client_loc_zh}的语言配置文件路径。\nPlease input a path of {patchline_loc_en} {client_loc_en} language configuration file.")
                else:
                    if product == "LoL":
                        if patchline == "live":
                            self.locPath_lol_ux_live = locPath_ux_tmp.replace("\\", "/")
                            self.config.set("paths", "loc_lol_live", self.locPath_lol_ux_live)
                        else:
                            self.locPath_lol_ux_pbe = locPath_ux_tmp.replace("\\", "/")
                            self.config.set("paths", "loc_lol_pbe", self.locPath_lol_ux_pbe)
                    else:
                        if patchline == "live":
                            self.locPath_tft_live = locPath_ux_tmp.replace("\\", "/")
                            self.config.set("paths", "loc_tft_live", self.locPath_tft_live)
                        else:
                            self.locPath_tft_pbe = locPath_ux_tmp.replace("\\", "/")
                            self.config.set("paths", "loc_tft_pbe", self.locPath_tft_pbe)
                    self.paths_ready[locPath_ux_key] = True
                    self.save_config()
                    break
        return self.paths_ready[locPath_ux_key]
    
    #定义进程运行情况检查方法族（Define process running status check method family）
    def check_running_rc(self) -> bool:
        '''
        检查是否有正在运行中的拳头客户端进程。<br>Check whether there's a running RiotClientServices.exe.
        
        :return: 是否有正在运行中的拳头客户端进程。<br>Whether there's a RiotClientServices.exe running.
        :rtype: bool
        '''
        isRunning: bool = False
        for process in psutil.process_iter():
            try:
                wd: str = process.exe()
            except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            else:
                if wd.replace("\\", "/") == self.rcPath:
                    isRunning = True
                    break
        return isRunning
    
    def check_running_client(self, product: str, patchline: str) -> bool:
        '''
        检查是否有正在运行中的联盟客户端或云顶客户端进程。<br>Check whether there's a running League Client or TFT Client process.
        
        :param product: 游戏产品。<br>Game product.
        
            - LoL: 英雄联盟
            - TFT: 云顶之弈
        :type product: Literal["LoL", "TFT"]
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否有正在运行中的联盟客户端或云顶客户端进程。<br>Whether there's a League Client or TFT Client process running.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if product != "TFT":
            product = "LoL"
        if patchline != "live":
            patchline = "pbe"
        #函数主体（Function body）
        if product == "TFT":
            clientPath: str = self.tftClientPath_live if patchline == "live" else self.tftClientPath_pbe
        else:
            clientPath = self.lolUxPath_live if patchline == "live" else self.lolUxPath_pbe
        isRunning: bool = False
        for process in psutil.process_iter():
            try:
                wd: str = process.exe()
            except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            else:
                if wd.replace("\\", "/") == clientPath:
                    isRunning = True
                    break
        return isRunning
    
    #定义YAML数据读取方法（Define YAML reading method）
    def read_rc_loc(self) -> bool:
        '''
        读取拳头客户端的语言配置。<br>Read Riot Client language configuration.
        
        :return: 是否成功读取文件。<br>Whether the file is successfully read.
        :rtype: bool
        '''
        try:
            with open(self.locPath_rc, "r", encoding = "utf-8") as fp:
                self.rc_loc_data: CommentedMap = self._yaml.load(fp)
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True
    
    def read_gt_loc(self, product: str, patchline: str) -> bool:
        '''
        读取联盟客户端或云顶客户端的游戏文本语言配置。<br>Read the game text language configuration of League Client or TFT Client.
        
        :param product: 游戏产品。<br>Game product.
        
            - LoL: 英雄联盟
            - TFT: 云顶之弈
        :type product: Literal["LoL", "TFT"]
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否成功读取文件。<br>Whether the file is successfully read.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if product != "TFT":
            product = "LoL"
        if patchline != "live":
            patchline = "pbe"
        if product == "TFT":
            locPath_gt: str = self.locPath_tft_live if patchline == "live" else self.locPath_tft_pbe
        else:
            locPath_gt = self.locPath_lol_ux_live if patchline == "live" else self.locPath_lol_ux_pbe
        #函数主体（Function body）
        try:
            with open(locPath_gt, "r", encoding = "utf-8") as fp:
                self.gt_loc_data: CommentedMap = self._yaml.load(fp)
        except FileNotFoundError: #在更新客户端的过程，可能会有一段短暂的时间，这个文件被删除（While the client is being updated, there might be short period of time when this file is deleted）
            self.error_count += 1
            print(f"[{self.error_count}]文件被删除。 | File deleted.")
            return False
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True
    
    #定义语言配置修改方法族（Define language configuration edit method family）
    def change_rc_language(self, data: Optional[CommentedMap] = None, locale: Optional[str] = None) -> None:
        '''
        将拳头客户端语言修改为简体中文。<br>Change Riot Client language into Chinese Simplified.
        
        :param data: 通过YAML对象读取的拳头客户端语言配置数据。如果未指定，则使用对象内的数据。<br>Riot Client language configuration data read by a YAML object. If it's unspecified, data inside the object will be used.
        :type data: CommentedMap
        :param locale: 目标语言文化代码。如果未指定，则使用对象属性。<br>Target language code. If it's unspecified, the object attribute will be used.
        :type locale: str
        '''
        #参数预处理（Parameter pre-processing）
        if data == None:
            data = self.rc_loc_data
        if locale == None:
            locale = self.locale
        #修改拳头客户端语言（Change the Riot Client language）
        if "install" in data and "localization" in data["install"] and "locale" in data["install"]["localization"]:
            data["install"]["localization"]["locale"] = locale
    
    def change_gt_language(self, data: Optional[CommentedMap] = None, locale: Optional[str] = None) -> None:
        '''
        将游戏文本语言修改为简体中文。<br>Change the game text language into Chinese Simplified.
        
        :param data: 通过YAML对象读取的英雄联盟或云顶之弈客户端语言配置数据。如果未指定，则使用对象内的数据。<br>language configuration data of League Client or TFT Client read by a YAML object. If it's unspecified, data inside the object will be used.
        :type data: CommentedMap
        :param locale: 目标语言文化代码。如果未指定，则使用对象属性。<br>Target language code. If it's unspecified, the object attribute will be used.
        :type locale: str
        '''
        #参数预处理（Parameter pre-processing）
        if data == None:
            data = self.gt_loc_data
        if locale == None:
            locale = self.locale
        #修改语言数据（Change locale data）
        if locale == "zh_CN" and "locale_data" in data: #因为只有中文（中国）没有出现在可用语言文化代码列表中，所以只需要针对中文（中国）进行讨论【Only zh_CN isn't present in the "available_locales" list, so only Chinese (China) needs to be discussed】
            #修改可用语言文化代码列表（Change the list of available locales）
            if "available_locales" in data["locale_data"] and not "zh_CN" in data["locale_data"]["available_locales"] and "zh_MY" in data["locale_data"]["available_locales"]:
                index: int = data["locale_data"]["available_locales"].index("zh_MY")
                data["locale_data"]["available_locales"].insert(index, DoubleQuotedScalarString("zh_CN"))
            #修改默认语言（Change the default language）
            if "default_locale" in data["locale_data"]:
                data["locale_data"]["default_locale"] = "zh_CN"
        #修改游戏文本语言（Change the game text language）
        if "settings" in data and "locale" in data["settings"]:
            data["settings"]["locale"] = locale
    
    #定义YAML数据导出方法（Define YAML data export methods）
    def write_rc_loc(self) -> bool:
        '''
        写入拳头客户端的语言配置。<br>Write Riot Client language configuration.
        
        :return: 是否成功写入文件。<br>Whether data are successfully written into the file.
        :rtype: bool
        '''
        try:
            with open(self.locPath_rc, "w", encoding = "utf-8") as fp:
                self._yaml.dump(self.rc_loc_data, fp)
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True
    
    def write_ux_loc(self, product: str, patchline: str) -> bool:
        '''
        写入联盟客户端或云顶客户端的游戏文本语言配置。<br>Write game text language configuration of League Client or TFT Client.
        
        :param product: 游戏产品。<br>Game product.
        
            - LoL: 英雄联盟
            - TFT: 云顶之弈
        :type product: Literal["LoL", "TFT"]
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否成功写入文件。<br>Whether data are successfully written into the file.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if product != "TFT":
            product = "LoL"
        if patchline != "live":
            patchline = "pbe"
        if product == "TFT":
            locPath_gt: str = self.locPath_tft_live if patchline == "live" else self.locPath_tft_pbe
        else:
            locPath_gt = self.locPath_lol_ux_live if patchline == "live" else self.locPath_lol_ux_pbe
        #函数主体（Function body）
        try:
            with open(locPath_gt, "w", encoding = "utf-8") as fp:
                self._yaml.dump(self.gt_loc_data, fp)
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True

def change_rc_locale(localeManager: LoLLocaleManager) -> int:
    '''
    通过一个语言管理器对象修改拳头客户端的语言配置。<br>Change Riot Client language configuration through a `LoLLocaleManager` object.
    
    :param localeManager: 一个语言管理器对象。<br>A `LoLLocaleManager` object.
    
        该对象需满足以下路径键的值为真：<br>Values of the following path keys of this object should be true:
        - locPath_rc
    :type localeManager: LoLLocaleManager
    :return: 状态码。<br>Status code.
    
        - 0: 成功读取文件和写入文件。<br>Successfully read the file and write data into it.
        - 1: 成功读取文件，但未发生写入操作。<br>Successfully read the file but no write operation is performed.
        - 2: 未能读取文件。<br>Fail to read the file.
        - 3: 成功读取文件，但未能写入文件。<br>Successfully read the file but fail to write data into it.
        - 4: 数据格式不正确。<br>Data format doesn't match.
    :rtype: int
    '''
    read_status: bool = localeManager.read_rc_loc()
    if read_status:
        tmp_ptr: Any = localeManager.rc_loc_data
        for subkey in ["install", "localization", "locale"]:
            if subkey in tmp_ptr:
                tmp_ptr = tmp_ptr[subkey]
            else:
                return 4
        else:
            if tmp_ptr == localeManager.locale:
                return 1
            else:
                localeManager.change_rc_language()
                write_status: bool = localeManager.write_rc_loc()
                return 0 if write_status else 3
    else:
        return 2

def change_gt_locale(localeManager: LoLLocaleManager, product: str, patchline: str) -> int:
    '''
    通过一个语言管理器对象来修改联盟客户端或云顶客户端的游戏文本语言配置。<br>Change the game text language configuration of League Client or TFT Client through a `LoLLocaleManager` object.
    
    :param localeManager: 一个语言管理器对象。<br>A `LoLLocaleManager` object.
    
        对于正式服联盟客户端，该对象需满足以下路径键的值为真：<br>For Live League Client, values of the following path keys of this object should be true:
        - rcPath
        - lolUxPath_live
        - locPath_lol_ux_live
        
        对于测试服联盟客户端，该对象需满足以下路径键的值为真：<br>For PBE League Client, values of the following path keys of this object should be true:
        - rcPath
        - lolUxPath_pbe
        - locPath_lol_ux_pbe

        对于正式服云顶客户端，该对象需满足以下路径键的值为真：<br>For Live TFT Client, values of the following path keys of this object should be true:
        - rcPath
        - tftClientPath_live
        - locPath_tft_live
        
        对于测试服云顶客户端，该对象需满足以下路径键的值为真：<br>For PBE TFT Client, values of the following path keys of this object should be true:
        - rcPath
        - tftClientPath_pbe
        - locPath_tft_pbe
    :type localeManager: LoLLocaleManager
    :param product: 游戏产品。<br>Game product.
    
        - LoL: 英雄联盟
        - TFT: 云顶之弈
    :type product: Literal["LoL", "TFT"]
    :param patchline: 游戏版本线。<br>Game patchline.
    
        - live: 正式服
        - pbe: 测试服
    :type patchline: Literal["live", "pbe"]
    :return: 状态码。<br>Status code.
    
        - 0: 成功读取文件和写入文件。<br>Successfully read the file and write data into it.
        - 1: 成功读取文件，但未发生写入操作。<br>Successfully read the file but no write operation is performed.
        - 2: 未能读取文件。<br>Fail to read the file.
        - 3: 成功读取文件，但未能写入文件。<br>Successfully read the file but fail to write data into it.
        - 4: 数据格式不正确。<br>Data format doesn't match.
    :rtype: int
    '''
    #参数预处理（Paramter pre-processing）
    if product != "TFT":
        product = "LoL"
    if patchline != "live":
        patchline = "pbe"
    #函数主体（Function body）
    read_status: bool = localeManager.read_gt_loc(product, patchline)
    if read_status:
        tmp_ptr: Any = localeManager.gt_loc_data
        for subkey in ["settings", "locale"]:
            if subkey in tmp_ptr:
                tmp_ptr = tmp_ptr[subkey]
            else:
                return 4
        else:
            if tmp_ptr == localeManager.locale:
                return 1
            else:
                localeManager.change_gt_language()
                write_status: bool = localeManager.write_ux_loc(product, patchline)
                return 0 if write_status else 3
    else:
        return 2

#定义主函数（Define the main function）
def main() -> None:
    print(f"当前配置文件（Current configuration file）：\n{args.config}")
    localeManager: LoLLocaleManager = LoLLocaleManager(args.locale, args.interval, args.config)
    localeManager.set_yaml_params()
    print("请选择您想要修改语言配置的客户端。\nPlease select the client to change language.\n-1\t设置（Settings）\n0\t退出程序（Exit the program）\n1\t拳头客户端（Riot Client）\n2\t联盟客户端——正式服（League Client - Live）\n3\t联盟客户端——测试服（League Client - PBE）\n4\t云顶客户端——正式服（TFT Client - Live）\n5\t云顶客户端——测试服（TFT Client - PBE）")
    while True:
        option: str = input()
        if option == "":
            continue
        elif option == "-1":
            print("请选择一个设置项：\nPlease select a settings option:\n0\t返回上一层（Return to the last step）\n1\t目标语言（Target language）\n2\t循环间隔（Loop interval）\n3\t切换程序配置文件（Switch program config file）")
            while True:
                settings_option: str = input()
                if settings_option == "":
                    continue
                elif settings_option[0] == "0":
                    break
                elif settings_option[0] == "1":
                    localeManager.set_locale()
                elif settings_option[0] == "2":
                    localeManager.set_interval()
                elif settings_option[0] == "3":
                    localeManager.set_config()
                else:
                    print("您的输入有误！请重新输入。\nERROR input. Please try again.")
                    continue
                print("请选择一个设置项：\nPlease select a settings option:\n0\t返回上一层（Return to the last step）\n1\t目标语言（Target language）\n2\t循环间隔（Loop interval）\n3\t切换程序配置文件（Switch program config file）")
        elif option[0] == "0":
            break
        elif option[0] == "1":
            ready: bool = localeManager.check_locPath_rc()
            if ready:
                status: int = change_rc_locale(localeManager)
                if status == 0:
                    print("已修改拳头客户端的语言配置。请重新启动拳头客户端。\nRiot Client language configuration has been changed. Please restart Riot Client.")
                elif status == 1:
                    print("当前拳头客户端的语言已经是目标语言了。程序未作任何处理。\nRiot Client is already in the target language. No operation has been performed.")
                elif status == 2:
                    print("读取拳头客户端语言配置文件的过程出现了一个问题。\nAn error occurred when the program read Riot Client language configuration file.")
                elif status == 3:
                    print("写入拳头客户端语言配置文件的过程出现了一个问题。\nAn error occurred when data were written into Riot Client language configuration file.")
                elif status == 4:
                    print("未找到语言选项。请联系开发人员检查语言键路径并更新程序。\nLanguage option not found. Please contact the developer to check the locale key path and update the program.")
                else:
                    print(f"未识别的状态码（{status}）。\nUnrecognized status code {status}.")
        elif option[0] in {"2", "3", "4", "5"}:
            product: str = "LoL" if option[0] in {"2", "3"} else "TFT"
            patchline: str = "pbe" if option[0] in {"3", "5"} else "live"
            client_loc_zh: str = "联盟客户端" if product == "LoL" else "云顶客户端"
            client_loc_en: str = "League Client" if product == "LoL" else "TFT Client"
            patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
            patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
            #检查客户端文件路径是否存在（Check whether client file paths exist）
            ready: bool = False
            for i in range(3):
                if i == 0:
                    ready = localeManager.check_rcPath()
                elif i == 1:
                    ready = localeManager.check_lolUxPath(patchline)
                else:
                    ready = localeManager.check_locPath_gt(product, patchline)
                if not ready: #当用户退出取消路径检查操作时，视为放弃修改语言配置（When the user cancels path check, the program regards the user cancels configuring the language）
                    break
            if ready:
                #确定运行模式（Determine the running mode）
                uxRunning: bool = localeManager.check_running_client(product, patchline)
                if uxRunning or product == "TFT": #当客户端正在运行时，只需要修改一次。另外，国际服的云顶客户端原生支持简体中文，因此也只需要修改一次就可生效（When the client is running, this change only needs making once）
                    status: int = change_gt_locale(localeManager, product, patchline)
                    if status == 0:
                        print(f"已修改{patchline_loc_zh}{client_loc_zh}的语言配置。请在拳头客户端已激活的情况下退出{client_loc_zh}，或者登出{client_loc_zh}。\n{patchline_loc_en} {client_loc_en} language configuration has been changed. Please exit {client_loc_en} ensuring Riot Client has been activated, or sign out of {client_loc_en}.")
                    elif status == 1:
                        print(f"{patchline_loc_zh}{client_loc_zh}的语言已经是目标语言了。程序未作任何处理。\n{patchline_loc_en} {client_loc_en} is already in the target language. No operation has been performed.")
                    elif status == 2:
                        print(f"读取{patchline_loc_zh}{client_loc_zh}语言配置文件的过程出现了一个问题。\nAn error occurred when the program read {patchline_loc_en} {client_loc_en} language configuration file.")
                    elif status == 3:
                        print(f"写入{patchline_loc_zh}{client_loc_zh}语言配置文件的过程出现了一个问题。\nAn error occurred when data were written into {patchline_loc_en} {client_loc_en} language configuration file.")
                    elif status == 4:
                        print("未找到语言选项。请联系开发人员检查语言键路径并更新程序。\nLanguage option not found. Please contact the developer to check the locale key path and update the program.")
                    else:
                        print(f"未识别的状态码（{status}）。\nUnrecognized status code {status}.")
                else:
                    print(f'正在循环修改{patchline_loc_zh}{client_loc_zh}的语言配置，直到{client_loc_zh}启动。按住“Esc”键可提前退出循环。\nChanging {patchline_loc_en} {client_loc_en} language configuration in a loop until {client_loc_en} is launched. Press and hold "Esc" to exit the loop in advance.\n当前循环间隔（Current loop interval）：{localeManager.interval} s.')
                    loop_count: int = 0 #统计循环的执行次数（Count the number of loops executed）
                    change_count: int = 0 #统计变更文件次数（Count the number of changed made）
                    status: int = 0 #初始化状态码以应对严格的类型检查模式（Initialize the status code in face of the strict type checking mode）
                    while not localeManager.check_running_client(product, patchline): #当客户端尚未运行时，需要一直修改，直到客户端启动（When the client isn't running, this change needs making all the time until the client is launched）
                        if isKeyPressed(b"\x1b"):
                            print("您已中断循环。程序将返回上一层。\nYou've terminated the loop. The program will return to the last step.")
                            break
                        loop_count += 1
                        print(f"[{loop_count}]", end = "\r")
                        status: int = change_gt_locale(localeManager, product, patchline)
                        if status == 0:
                            change_count += 1
                            print(f"第{change_count}次修改{patchline_loc_zh}{client_loc_zh}的语言配置。\nNumber of times of changing {patchline_loc_en} {client_loc_en} language configuration: {change_count}.")
                        time.sleep(localeManager.interval)
                    else: #如果因为按下“Esc”键导致程序退出while循环，则程序不会运行此部分（If the program exits the while-loop because the user presses "Esc", then this part won't be executed）
                        print(f"已修改{patchline_loc_zh}{client_loc_zh}的语言配置。\n{patchline_loc_en} {client_loc_en} language configuration has been changed.")
                        print(f"{patchline_loc_zh}{client_loc_zh}进程已启动。程序已退出循环。\n{patchline_loc_en} {client_loc_en} has launched. The program has exited the loop.")
        else:
            print("您的输入有误！请重新输入。\nERROR input! Please try again.")
            continue
        localeManager.init_loc_data()
        print("请选择您想要修改语言配置的客户端。\nPlease select the client to change language.\n-1\t设置（Settings）\n0\t退出程序（Exit the program）\n1\t拳头客户端（Riot Client）\n2\t联盟客户端——正式服（League Client - Live）\n3\t联盟客户端——测试服（League Client - PBE）\n4\t云顶客户端——正式服（TFT Client - Live）\n5\t云顶客户端——测试服（TFT Client - PBE）")

if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter)
    parser.add_argument("-l", "--locale", help = "拳头客户端、联盟客户端和云顶客户端的语言。\nLanguage of Riot Client, League Client and TFT Client.", action = "store", type = str, choices = AVAILABLE_LOCALES, default = "zh_CN") #本程序目前默认拳头客户端和联盟客户端采用相同语言。本程序主要面向中国大陆用户，因为其它语言可直接在拳头客户端中修改。所以默认语言为中文（中国）【This program uses the same language for Riot Client and League Client. This program is mainly oriented to Chinese Mainland users, for other languages can be directly changed in Riot Client. Therefore, the default language is Chinese (China)】
    parser.add_argument("-i", "--interval", help = "检测yaml文件变更的间隔（秒）。\nThe time interval for detecting whether the yaml file is changed, in seconds.", action = "store", type = float, default = 0.5)
    parser.add_argument("-c", "--config", help = f"配置文件路径。默认是{DEFAULT_CONFIG_PATH}。\nPath of the configuration file. Default: {DEFAULT_CONFIG_PATH}.", action = "store", type = str, default = DEFAULT_CONFIG_PATH)
    args: argparse.Namespace = parser.parse_args()

    main()
