import argparse, msvcrt, os, psutil, time
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString #使得列表元素强制使用双引号【Force to use double quotes for an element in a list (CommentedSeq)】
from typing import Any, Optional
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.nodes import ScalarNode

AVAILABLE_LOCALES: list[str] = ["ar_AE", "cs_CZ", "el_GR", "pL_PL", "ro_RO", "hu_HU", "en_GB", "de_DE", "es_ES", "it_IT", "fr_FR", "ja_JP", "ko_KR", "es_MX", "es_AR", "pt_BR", "en_US", "en_AU", "ru_RU", "tr_TR", "ms_MY", "en_PH", "en_SG", "th_TH", "vi_VN", "id_ID", "zh_MY", "zh_CN", "zh_TW"]
RIOT_CLIENT_PATH: str = "C:/Riot Games/Riot Client/RiotClientServices.exe"
RC_LOC_PATH: str = os.path.expanduser("~/AppData/Local/Riot Games/Riot Client/Config/RiotClientSettings.yaml").replace("\\", "/")
LIVE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.live/league_of_legends.live.product_settings.yaml"
PBE_LOC_PATH: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.pbe/league_of_legends.pbe.product_settings.yaml"
LIVE_UX_PATH: str = "C:/Riot Games/League of Legends/LeagueClientUx.exe"
PBE_UX_PATH: str = "C:/Riot Games/League of Legends (PBE)/LeagueClientUx.exe"

def isKeyPressed(keyCode1: bytes, keyCode2: bytes = b"") -> bool:
    return bool(msvcrt.kbhit()) and msvcrt.getch() == keyCode1 and (keyCode1 != b"\xe0" and keyCode1 != b"\000" or msvcrt.getch() == keyCode2)

class LoLLocaleManager:
    def __init__(self, locale: str = "zh_CN", interval: float = 0.5) -> None:
        '''
        构建一个语言管理器对象。<br>Construct a `LoLLocaleManager` object.
        
        :param locale: 目标语言文化代码。默认为中文（中国）。<br>Target language code. Chinese (China) by default.
        :type locale: str
        :param interval: 循环修改模式下检测yaml文件变更的间隔（单位：秒）。默认为0.5秒。<br>The time interval to detect whether the yaml file is changed under Loop Edit Mode, in seconds. 0.5 seconds by default.
        :type interval: float
        '''
        self.locale: str = locale #目标语言文化代码（Target language code）
        self.interval: float = interval #循环修改时的读取间隔（Time interval between two reads in Loop Edit mode）
        self.rcPath: str = "C:/Riot Games/Riot Client/RiotClientServices.exe" #拳头客户端的可执行文件路径（Path of Riot Client executable）
        self.uxPath_live: str = "C:/Riot Games/League of Legends/LeagueClientUx.exe" #正式服联盟客户端用户体验界面可执行文件路径（Path of Live League Client User Experience executable file）
        self.uxPath_pbe: str = "C:/Riot Games/League of Legends (PBE)/LeagueClientUx.exe" #测试服联盟客户端用户体验界面可执行文件路径（Path of PBE League Client User Experience executable file）
        self.locPath_rc: str = os.path.expanduser("~/AppData/Local/Riot Games/Riot Client/Config/RiotClientSettings.yaml").replace("\\", "/") #拳头客户端语言配置文件路径（Path of Riot Client language configuration file）
        self.locPath_ux_live: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.live/league_of_legends.live.product_settings.yaml" #正式服语言配置文件的路径（Path of Live League Client language configuration file）
        self.locPath_ux_pbe: str = "C:/ProgramData/Riot Games/Metadata/league_of_legends.pbe/league_of_legends.pbe.product_settings.yaml" #测试服语言配置文件的路径（Path of PBE League Client language configuration file）
        self.paths_ready: dict[str, bool] = {"rcPath": False, "uxPath_live": False, "uxPath_pbe": False, "locPath_rc": False, "locPath_ux_live": False, "locPath_ux_pbe": False} #各路径是否存在（Whether each path exists）
        self.yaml: YAML = YAML() #初始化YAML读取引擎（Initialize YAML reading engine）
        self.rc_loc_data: CommentedMap = CommentedMap() #初始化拳头客户端语言配置数据（Initialize Riot Client language configuration data）
        self.ux_loc_data: CommentedMap = CommentedMap() #初始化联盟客户端语言配置数据（Initialize League Client language configuration data）
        self.error_count: int = 0 #错误次数（Number of errors）
    
    def init_data(self) -> None:
        '''
        初始化语言配置数据。<br>Initialize language configuration data.
        '''
        self.rc_loc_data = CommentedMap()
        self.ux_loc_data = CommentedMap()
        self.error_count = 0
    
    #定义YAML引擎参数调整方法（Define a YAML engine parameter adjustment method）
    def set_yaml_params(self, mapping: int = 4, sequence: int = 4, offset: int = 2, preserve_quotes: bool = True, width: int = 4096) -> None:
        '''
        调整YAML引擎的参数。<br>Adjust parameters of the YAML engine.
        
        :param mapping: 每个键值对的值前空格与键前空格之间的差值。默认为4个空格。<br>The difference of the number of spaces between in front of the key and in front of the value. 4 spaces by default.
        :type mapping: int
        :param sequence: 列表项的缩进空格
        '''
        self.yaml.indent(mapping = mapping, sequence = sequence, offset = offset)
        self.yaml.preserve_quotes = preserve_quotes
        self.yaml.width = width
        def represent_none(self: RoundTripRepresenter, data: None) -> ScalarNode:
            '''
            YAML引擎的空值处理策略。<br>Empty value handling strategy of YAML engine.
            '''
            return self.represent_scalar("tag:yaml.org,2002:null", "null")
        self.yaml.representer.add_representer(type(None), represent_none)
    
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
                    break
        return self.paths_ready["rcPath"]

    def check_uxPath(self, patchline: str) -> bool:
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
        uxPath: str = self.uxPath_live if patchline == "live" else self.uxPath_pbe
        uxPath_key: str = "uxPath_live" if patchline == "live" else "uxPath_pbe"
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
                        self.uxPath_live = uxPath_tmp.replace("\\", "/")
                    else:
                        self.uxPath_pbe = uxPath_tmp.replace("\\", "/")
                    self.paths_ready[uxPath_key] = True
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
                    break
        return self.paths_ready["locPath_rc"]
    
    def check_locPath_ux(self, patchline: str) -> bool:
        '''
        检查正式服联盟客户端语言配置文件路径。如果路径不存在，则要求用户修改。<br>Check the path of Live League Client language configuration file. If it doesn't exist, then this function asks the user to change it.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 正式服联盟客户端的语言配置文件是否准备就绪。<br>Whether Live League Client language configuration file is ready.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        locPath_ux: str = self.locPath_ux_live if patchline == "live" else self.locPath_ux_pbe
        locPath_ux_key: str = "locPath_ux_live" if patchline == "live" else "locPath_ux_pbe"
        patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
        patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
        #函数主体（Function body）
        if os.path.exists(locPath_ux):
            self.paths_ready[locPath_ux_key] = True
        else:
            print(f"请指定{patchline_loc_zh}联盟客户端的语言配置文件路径。例如：\nPlease specify an existing path of {patchline_loc_en} League Client language configuration file. Example:\n{locPath_ux}")
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
                elif not os.path.basename(locPath_ux_tmp) == f"league_of_legends.{patchline}.product_settings.yaml":
                    print(f"请输入{patchline_loc_zh}联盟客户端的语言配置文件路径。\nPlease input a path of {patchline_loc_en} League Client language configuration file.")
                else:
                    if patchline == "live":
                        self.locPath_ux_live = locPath_ux_tmp.replace("\\", "/")
                    else:
                        self.locPath_ux_pbe = locPath_ux_tmp.replace("\\", "/")
                    self.paths_ready[locPath_ux_key] = True
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
    
    def check_running_ux(self, patchline: str) -> bool:
        '''
        检查是否有正在运行中的联盟客户端用户体验进程。<br>Check whether there's a running LeagueClientUx.exe.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否有正在运行中的联盟客户端用户体验进程。<br>Whether there's a LeagueClientUx.exe running.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        #函数主体（Function body）
        uxPath: str = self.uxPath_live if patchline == "live" else self.uxPath_pbe
        isRunning: bool = False
        for process in psutil.process_iter():
            try:
                wd: str = process.exe()
            except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            else:
                if wd.replace("\\", "/") == uxPath:
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
                self.rc_loc_data: CommentedMap = self.yaml.load(fp)
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True
    
    def read_ux_loc(self, patchline: str) -> bool:
        '''
        读取联盟客户端的语言配置。<br>Read League Client language configuration.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否成功读取文件。<br>Whether the file is successfully read.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        locPath_ux: str = self.locPath_ux_live if patchline == "live" else self.locPath_ux_pbe
        #函数主体（Function body）
        try:
            with open(locPath_ux, "r", encoding = "utf-8") as fp:
                self.ux_loc_data: CommentedMap = self.yaml.load(fp)
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
    
    def change_ux_language(self, data: Optional[CommentedMap] = None, locale: Optional[str] = None) -> None:
        '''
        将游戏文本语言修改为简体中文。<br>Change the game text language into Chinese Simplified.
        
        :param data: 通过YAML对象读取的英雄联盟客户端语言配置数据。如果未指定，则使用对象内的数据。<br>League Client language configuration data read by a YAML object. If it's unspecified, data inside the object will be used.
        :type data: CommentedMap
        :param locale: 目标语言文化代码。如果未指定，则使用对象属性。<br>Target language code. If it's unspecified, the object attribute will be used.
        :type locale: str
        '''
        #参数预处理（Parameter pre-processing）
        if data == None:
            data = self.ux_loc_data
        if locale == None:
            locale = self.locale
        #修改语言数据（Change locale data）
        if locale == "zh_CN" and "locale_data" in data: #因为只有中文（中国）没有出现在可用语言文化代码列表中，所以只需要针对中文（中国）进行讨论【Only zh_CN isn't present in the "available_locales" list, so only Chinese (China) needs to be discussed】
            #修改可用语言文化代码列表（Change the list of available locales）
            if "available_locales" in data["locale_data"] and "zh_MY" in data["locale_data"]["available_locales"]:
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
                self.yaml.dump(self.rc_loc_data, fp)
        except PermissionError:
            self.error_count += 1
            print(f"[{self.error_count}]拒绝访问。 | Access Denied.")
            return False
        else:
            return True
    
    def write_ux_loc(self, patchline: str) -> bool:
        '''
        写入联盟客户端的语言配置。<br>Write League Client language configuration.
        
        :param patchline: 游戏版本线。<br>Game patchline.
        
            - live: 正式服
            - pbe: 测试服
        :type patchline: Literal["live", "pbe"]
        :return: 是否成功写入文件。<br>Whether data are successfully written into the file.
        :rtype: bool
        '''
        #参数预处理（Paramter pre-processing）
        if patchline != "live":
            patchline = "pbe"
        locPath_ux: str = self.locPath_ux_live if patchline == "live" else self.locPath_ux_pbe
        #函数主体（Function body）
        try:
            with open(locPath_ux, "w", encoding = "utf-8") as fp:
                self.yaml.dump(self.ux_loc_data, fp)
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

def change_ux_locale(localeManager: LoLLocaleManager, patchline: str) -> int:
    '''
    通过一个语言管理器对象来修改联盟客户端的语言配置。<br>Change League Client language configuration through a `LoLLocaleManager` object.
    
    :param localeManager: 一个语言管理器对象。<br>A `LoLLocaleManager` object.
    
        对于正式服，该对象需满足以下路径键的值为真：<br>For Live, values of the following path keys of this object should be true:
        - rcPath
        - uxPath_live
        - locPath_ux_live
        
        对于测试服，该对象需满足以下路径键的值为真：<br>For PBE, values of the following path keys of this object should be true:
        - rcPath
        - uxPath_pbe
        - locPath_ux_pbe
    :type localeManager: LoLLocaleManager
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
    if patchline != "live":
        patchline = "pbe"
    #函数主体（Function body）
    read_status: bool = localeManager.read_ux_loc(patchline)
    if read_status:
        tmp_ptr: Any = localeManager.ux_loc_data
        for subkey in ["settings", "locale"]:
            if subkey in tmp_ptr:
                tmp_ptr = tmp_ptr[subkey]
            else:
                return 4
        else:
            if tmp_ptr == localeManager.locale:
                return 1
            else:
                localeManager.change_ux_language()
                write_status: bool = localeManager.write_ux_loc(patchline)
                return 0 if write_status else 3
    else:
        return 2

def main() -> None:
    localeManager: LoLLocaleManager = LoLLocaleManager(args.locale, args.interval)
    localeManager.set_yaml_params()
    print("请选择您想要修改语言配置的客户端。\nPlease select the client to change language.\n1\t拳头客户端（Riot Client）\n2\t联盟客户端——正式服（League Client - Live）\n3\t联盟客户端——测试服（League Client - PBE）")
    while True:
        option: str = input()
        if option == "":
            continue
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
        elif option[0] == "2" or option[0] == "3":
            patchline: str = "pbe" if option[0] == "3" else "live"
            patchline_loc_zh: str = "正式服" if patchline == "live" else "测试服"
            patchline_loc_en: str = "Live" if patchline == "live" else "PBE"
            #检查客户端文件路径是否存在（Check whether client file paths exist）
            ready: bool = False
            for i in range(3):
                if i == 0:
                    ready = localeManager.check_rcPath()
                elif i == 1:
                    ready = localeManager.check_uxPath(patchline)
                else:
                    ready = localeManager.check_locPath_ux(patchline)
                if not ready: #当用户退出取消路径检查操作时，视为放弃修改语言配置（When the user cancels path check, the program regards the user cancels configuring the language）
                    break
            if ready:
                #确定运行模式（Determine the running mode）
                uxRunning: bool = localeManager.check_running_ux(patchline)
                if uxRunning: #当联盟客户端正在运行时，只需要修改一次（When League Client is running, this change only needs making once）
                    status: int = change_ux_locale(localeManager, patchline)
                    if status == 0:
                        print(f"已修改{patchline_loc_zh}联盟客户端的语言配置。请在拳头客户端已激活的情况下退出联盟客户端，或者登出联盟客户端。\n{patchline_loc_en} League Client language configuration has been changed. Please exit League Client ensuring Riot Client has been activated, or sign out of League Client.")
                    elif status == 1:
                        print(f"{patchline_loc_zh}联盟客户端的语言已经是目标语言了。程序未作任何处理。\n{patchline_loc_en} League Client is already in the target language. No operation has been performed.")
                    elif status == 2:
                        print(f"读取{patchline_loc_zh}联盟客户端语言配置文件的过程出现了一个问题。\nAn error occurred when the program read {patchline_loc_en} League Client language configuration file.")
                    elif status == 3:
                        print(f"写入{patchline_loc_zh}联盟客户端语言配置文件的过程出现了一个问题。\nAn error occurred when data were written into {patchline_loc_en} League Client language configuration file.")
                    elif status == 4:
                        print("未找到语言选项。请联系开发人员检查语言键路径并更新程序。\nLanguage option not found. Please contact the developer to check the locale key path and update the program.")
                    else:
                        print(f"未识别的状态码（{status}）。\nUnrecognized status code {status}.")
                else:
                    print(f'正在循环修改{patchline_loc_zh}联盟客户端的语言配置，直到联盟客户端启动。按住“Esc”键可提前退出循环。\nChanging {patchline_loc_en} League Client language configuration in a loop until League Client is launched. Press and hold "Esc" to exit the loop in advance.\n当前循环间隔（Current loop interval）：{localeManager.interval} s.')
                    loop_count: int = 0 #统计循环的执行次数（Count the number of loops executed）
                    change_count: int = 0 #统计变更文件次数（Count the number of changed made）
                    status: int = 0 #初始化状态码以应对严格的类型检查模式（Initialize the status code in face of the strict type checking mode）
                    while not localeManager.check_running_ux(patchline): #当联盟客户端尚未运行时，需要一直修改，直到客户端启动（When League Client isn't running, this change needs making all the time until the client is launched）
                        if isKeyPressed(b"\x1b"):
                            print("您已中断循环。程序将返回上一层。\nYou've terminated the loop. The program will return to the last step.")
                            break
                        loop_count += 1
                        print(f"[{loop_count}]", end = "\r")
                        status: int = change_ux_locale(localeManager, patchline)
                        if status == 0:
                            change_count += 1
                            print(f"第{change_count}次修改{patchline_loc_zh}联盟客户端的语言配置。\nNumber of times of changing {patchline_loc_en} League Client language configuration: {change_count}.")
                        time.sleep(localeManager.interval)
                    else: #如果因为按下“Esc”键导致程序退出while循环，则程序不会运行此部分（If the program exits the while-loop because the user presses "Esc", then this part won't be executed）
                        print(f"已修改{patchline_loc_zh}联盟客户端的语言配置。\n{patchline_loc_en} League Client language configuration has been changed.")
                        print(f"{patchline_loc_zh}联盟客户端进程已启动。程序已退出循环。\n{patchline_loc_en} League Client has launched. The program has exited the loop.")
        else:
            print("您的输入有误！请重新输入。\nERROR input! Please try again.")
            continue
        localeManager.init_data()
        print("请选择您想要修改语言配置的客户端。\nPlease select the client to change language.\n1\t拳头客户端（Riot Client）\n2\t联盟客户端——正式服（League Client - Live）\n3\t联盟客户端——测试服（League Client - PBE）")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--locale", help = "拳头客户端和联盟客户端的语言（Language of Riot Client and League Client）", action = "store", type = str, choices = AVAILABLE_LOCALES, default = "zh_CN") #本程序目前默认拳头客户端和联盟客户端采用相同语言。本程序主要面向中国大陆用户，因为其它语言可直接在拳头客户端中修改。所以默认语言为中文（中国）【This program uses the same language for Riot Client and League Client. This program is mainly oriented to Chinese Mainland users, for other languages can be directly changed in Riot Client. Therefore, the default language is Chinese (China)】
    parser.add_argument("-i", "--interval", help = "检测yaml文件变更的间隔（秒）（The time interval for detecting whether the yaml file is changed, in seconds）", action = "store", type = float, default = 0.5)
    args = parser.parse_args()

    main()
